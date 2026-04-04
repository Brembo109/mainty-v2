from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils import timezone

from .forms import LoginForm, StyledPasswordChangeForm, StyledSetPasswordForm


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
