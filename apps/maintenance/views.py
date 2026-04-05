from datetime import date

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Max, Q
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView, View

from apps.accounts.constants import Role
from apps.accounts.mixins import WriteAccessMixin

from .forms import MaintenancePlanCreateForm, MaintenancePlanUpdateForm, MaintenanceRecordForm
from .models import MaintenancePlan, MaintenanceRecord


def _plan_qs():
    """Base queryset with last_performed_at annotation to avoid N+1."""
    return MaintenancePlan.objects.select_related("asset").annotate(
        last_performed_at=Max("records__performed_at")
    )


class MaintenancePlanListView(LoginRequiredMixin, ListView):
    template_name = "maintenance/plan_list.html"
    context_object_name = "plans"
    paginate_by = 25

    def get_queryset(self):
        return _apply_filters(_plan_qs(), self.request.GET)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["can_write"] = self.request.user.has_role(Role.ADMIN, Role.USER)
        ctx["q"] = self.request.GET.get("q", "")
        ctx["status_filter"] = self.request.GET.get("status", "")
        get_params = self.request.GET.copy()
        get_params.pop("page", None)
        ctx["filter_params"] = get_params.urlencode()
        return ctx

    def render_to_response(self, context, **kwargs):
        if self.request.headers.get("HX-Request"):
            return TemplateResponse(
                self.request, "maintenance/partials/_plan_table.html", context
            )
        return super().render_to_response(context, **kwargs)


class MaintenancePlanDetailView(LoginRequiredMixin, DetailView):
    template_name = "maintenance/plan_detail.html"
    context_object_name = "plan"

    def get_queryset(self):
        return _plan_qs()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["can_write"] = self.request.user.has_role(Role.ADMIN, Role.USER)
        ctx["records"] = self.object.records.select_related("performed_by").order_by("-performed_at")
        ctx["record_form"] = MaintenanceRecordForm(
            initial={"performed_at": date.today(), "performed_by": self.request.user}
        )
        return ctx


class MaintenancePlanCreateView(LoginRequiredMixin, WriteAccessMixin, CreateView):
    form_class = MaintenancePlanCreateForm
    template_name = "maintenance/plan_form.html"

    def get_success_url(self):
        return reverse("maintenance:detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form_title"] = _("Neuer Wartungsplan")
        ctx["submit_label"] = _("Wartungsplan erstellen")
        return ctx

    def form_valid(self, form):
        messages.success(self.request, _("Wartungsplan wurde erfolgreich erstellt."))
        return super().form_valid(form)


class MaintenancePlanUpdateView(LoginRequiredMixin, WriteAccessMixin, UpdateView):
    form_class = MaintenancePlanUpdateForm
    template_name = "maintenance/plan_form.html"

    def get_queryset(self):
        return MaintenancePlan.objects.select_related("asset")

    def get_success_url(self):
        return reverse("maintenance:detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form_title"] = _("Wartungsplan bearbeiten")
        ctx["submit_label"] = _("Änderungen speichern")
        ctx["is_update"] = True
        return ctx

    def form_valid(self, form):
        messages.success(self.request, _("Wartungsplan wurde aktualisiert."))
        return super().form_valid(form)


class MaintenancePlanDeleteView(LoginRequiredMixin, WriteAccessMixin, DeleteView):
    model = MaintenancePlan
    template_name = "maintenance/plan_confirm_delete.html"
    context_object_name = "plan"
    success_url = reverse_lazy("maintenance:list")

    def form_valid(self, form):
        messages.success(self.request, _("Wartungsplan wurde gelöscht."))
        return super().form_valid(form)


class MaintenanceRecordCreateView(LoginRequiredMixin, WriteAccessMixin, View):
    """Create a maintenance record for a plan. Redirects back to plan detail."""

    def post(self, request, pk):
        plan = get_object_or_404(MaintenancePlan, pk=pk)
        form = MaintenanceRecordForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            record.plan = plan
            record.save()
            messages.success(request, _("Wartungsdurchführung wurde erfasst."))
        else:
            messages.error(request, _("Fehler beim Speichern — bitte Eingaben prüfen."))
        return redirect(reverse("maintenance:detail", kwargs={"pk": pk}))


# ---------------------------------------------------------------------------
# Shared filter logic
# ---------------------------------------------------------------------------

def _apply_filters(qs, get_params):
    q = get_params.get("q", "").strip()
    status = get_params.get("status", "").strip()

    if q:
        qs = qs.filter(
            Q(title__icontains=q)
            | Q(asset__name__icontains=q)
            | Q(responsible__icontains=q)
        )
    # Status filtering is done in Python after fetching because next_due depends
    # on annotated last_performed_at — DB-side date math would be complex.
    # For list sizes typical in GMP (< 500 plans), this is acceptable.
    if status:
        qs = list(qs)
        qs = [p for p in qs if p.status == status]
    return qs
