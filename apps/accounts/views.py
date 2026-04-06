from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, DetailView, FormView, ListView, UpdateView, View

from apps.audit.models import AuditLog
from .constants import Role
from .forms import AdminSetPasswordForm, LoginForm, StyledPasswordChangeForm, StyledSetPasswordForm, UserCreateForm, UserUpdateForm
from .mixins import RoleRequiredMixin
from .models import User


class LoginView(auth_views.LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True
    next_page = reverse_lazy("index")


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy("accounts:login")


class PasswordChangeView(auth_views.PasswordChangeView):
    template_name = "accounts/password_change.html"
    success_url = reverse_lazy("accounts:password_change_done")
    form_class = StyledPasswordChangeForm

    def form_valid(self, form):
        response = super().form_valid(form)
        # Reset the expiry clock on successful password change
        self.request.user.password_changed_at = timezone.now()
        self.request.user.save(update_fields=["password_changed_at"])
        return response


class PasswordChangeDoneView(LoginRequiredMixin, auth_views.PasswordChangeDoneView):
    template_name = "accounts/password_change_done.html"


class PasswordResetView(auth_views.PasswordResetView):
    template_name = "accounts/password_reset.html"
    email_template_name = "accounts/emails/password_reset_email.txt"
    subject_template_name = "accounts/emails/password_reset_subject.txt"
    success_url = reverse_lazy("accounts:password_reset_done")


class PasswordResetDoneView(auth_views.PasswordResetDoneView):
    template_name = "accounts/password_reset_done.html"


class PasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = "accounts/password_reset_confirm.html"
    success_url = reverse_lazy("accounts:password_reset_complete")
    form_class = StyledSetPasswordForm

    def form_valid(self, form):
        # Set before super() so form.save()'s single user.save() captures this field,
        # avoiding a second DB write and any race window.
        form.user.password_changed_at = timezone.now()
        return super().form_valid(form)


class PasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    template_name = "accounts/password_reset_complete.html"


class PasswordExpiredView(PasswordChangeView):
    """Force-password-change view shown when the 90-day rotation deadline is reached.

    Inherits all behaviour from PasswordChangeView (form validation, session
    re-auth, password_changed_at reset); only the template and redirect differ.
    """

    template_name = "accounts/password_expired.html"
    success_url = reverse_lazy("index")


@login_required
@require_POST
def set_theme(request):
    theme = request.POST.get("theme")
    if theme in ("dark", "light"):
        request.user.theme = theme
        request.user.save(update_fields=["theme"])
    next_url = request.POST.get("next") or "/"
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        next_url = "/"
    return redirect(next_url)


class UserListView(RoleRequiredMixin, ListView):
    required_role = Role.ADMIN
    model = User
    template_name = "accounts/user_list.html"
    context_object_name = "users"

    def get_queryset(self):
        return User.objects.prefetch_related("groups").order_by("username")


class UserCreateView(RoleRequiredMixin, CreateView):
    required_role = Role.ADMIN
    model = User
    form_class = UserCreateForm
    template_name = "accounts/user_form.html"
    success_url = reverse_lazy("accounts:user-list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form_title"] = _("Neuen Benutzer anlegen")
        ctx["submit_label"] = _("Benutzer erstellen")
        return ctx

    def form_valid(self, form):
        messages.success(self.request, _("Benutzer wurde erfolgreich erstellt."))
        return super().form_valid(form)


class UserDetailView(RoleRequiredMixin, DetailView):
    required_role = Role.ADMIN
    model = User
    template_name = "accounts/user_detail.html"
    context_object_name = "target_user"

    def get_queryset(self):
        return User.objects.prefetch_related("groups")


class UserUpdateView(RoleRequiredMixin, UpdateView):
    required_role = Role.ADMIN
    model = User
    form_class = UserUpdateForm
    template_name = "accounts/user_form.html"
    context_object_name = "target_user"
    success_url = reverse_lazy("accounts:user-list")

    def get_queryset(self):
        return User.objects.prefetch_related("groups")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form_title"] = _("Benutzer bearbeiten")
        ctx["submit_label"] = _("Änderungen speichern")
        return ctx

    def form_valid(self, form):
        messages.success(self.request, _("Benutzer wurde erfolgreich aktualisiert."))
        return super().form_valid(form)


class UserPasswordView(RoleRequiredMixin, FormView):
    required_role = Role.ADMIN
    template_name = "accounts/user_password.html"
    form_class = AdminSetPasswordForm

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.target_user = get_object_or_404(User, pk=kwargs["pk"])

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["target_user"] = self.target_user
        return ctx

    def form_valid(self, form):
        user = self.target_user
        user.set_password(form.cleaned_data["new_password1"])
        user.password_changed_at = timezone.now()
        user.save(update_fields=["password", "password_changed_at"])
        messages.success(self.request, _("Passwort wurde erfolgreich gesetzt."))
        return redirect("accounts:user-detail", pk=user.pk)


class UserToggleActiveView(RoleRequiredMixin, View):
    required_role = Role.ADMIN

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        user.is_active = not user.is_active
        user.save(update_fields=["is_active"])
        if user.is_active:
            messages.success(request, _("Benutzer %(username)s wurde aktiviert.") % {"username": user.username})
        else:
            messages.success(request, _("Benutzer %(username)s wurde deaktiviert.") % {"username": user.username})
        return redirect("accounts:user-list")


class UserDeleteView(RoleRequiredMixin, DeleteView):
    required_role = Role.ADMIN
    model = User
    template_name = "accounts/user_confirm_delete.html"
    context_object_name = "target_user"
    success_url = reverse_lazy("accounts:user-list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["has_audit_entries"] = AuditLog.objects.filter(actor=self.object).exists()
        return ctx

    def form_valid(self, form):
        if AuditLog.objects.filter(actor=self.object).exists():
            ctx = self.get_context_data()
            return self.render_to_response(ctx)
        messages.success(self.request, _("Benutzer %(username)s wurde gelöscht.") % {"username": self.object.username})
        self.object.delete()
        return redirect(self.success_url)
