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
from apps.accounts.mixins import RoleRequiredMixin, WriteAccessMixin
from apps.core.filters import build_toolbar_context

from .filter_defs import MAINTENANCE_FILTER_DIMENSIONS
from .forms import (
    MaintenancePlanCreateForm,
    MaintenancePlanFilterForm,
    MaintenancePlanUpdateForm,
    MaintenanceRecordForm,
)
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
        return _apply_filters(_plan_qs(), self._filter_form())

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        form = self._filter_form()
        ctx["filter_form"] = form
        ctx["can_write"] = self.request.user.has_role(Role.ADMIN, Role.USER)
        get_params = self.request.GET.copy()
        get_params.pop("page", None)
        ctx["filter_params"] = get_params.urlencode()
        ctx.update(build_toolbar_context(
            self.request, form, MAINTENANCE_FILTER_DIMENSIONS,
            search_placeholder=_("Bezeichnung, Anlage…"),
            hx_target="#plan-list-body",
            inline_fields=["status", "asset", "responsible"],
        ))
        return ctx

    def render_to_response(self, context, **kwargs):
        if self.request.headers.get("HX-Request") and not self.request.headers.get("HX-Boosted"):
            return TemplateResponse(
                self.request, "maintenance/partials/_plan_list_body.html", context
            )
        return super().render_to_response(context, **kwargs)

    def _filter_form(self):
        if not hasattr(self, "_cached_filter_form"):
            self._cached_filter_form = MaintenancePlanFilterForm(self.request.GET or None)
        return self._cached_filter_form


class MaintenancePlanDetailView(LoginRequiredMixin, DetailView):
    template_name = "maintenance/plan_detail.html"
    context_object_name = "plan"

    def get_queryset(self):
        return _plan_qs()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["can_write"] = self.request.user.has_role(Role.ADMIN, Role.USER)
        ctx["can_admin"] = self.request.user.has_role(Role.ADMIN)
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


class MaintenanceRecordUpdateView(LoginRequiredMixin, RoleRequiredMixin, UpdateView):
    model = MaintenanceRecord
    form_class = MaintenanceRecordForm
    template_name = "maintenance/record_form.html"
    context_object_name = "record"
    required_role = Role.ADMIN

    def get_object(self, queryset=None):
        return get_object_or_404(
            MaintenanceRecord.objects.select_related("plan"),
            pk=self.kwargs["record_pk"],
            plan_id=self.kwargs["pk"],
        )

    def get_success_url(self):
        return reverse("maintenance:detail", kwargs={"pk": self.kwargs["pk"]})

    def form_valid(self, form):
        messages.success(self.request, _("Wartungsdurchführung wurde aktualisiert."))
        return super().form_valid(form)


class MaintenanceRecordDeleteView(LoginRequiredMixin, RoleRequiredMixin, DeleteView):
    model = MaintenanceRecord
    template_name = "maintenance/record_confirm_delete.html"
    context_object_name = "record"
    required_role = Role.ADMIN

    def get_object(self, queryset=None):
        return get_object_or_404(
            MaintenanceRecord.objects.select_related("plan"),
            pk=self.kwargs["record_pk"],
            plan_id=self.kwargs["pk"],
        )

    def get_success_url(self):
        return reverse("maintenance:detail", kwargs={"pk": self.kwargs["pk"]})

    def form_valid(self, form):
        messages.success(self.request, _("Wartungsdurchführung wurde gelöscht."))
        return super().form_valid(form)


# ---------------------------------------------------------------------------
# Shared filter logic
# ---------------------------------------------------------------------------

def _apply_filters(qs, form):
    if not form.is_valid():
        return qs
    cd = form.cleaned_data
    if cd.get("q"):
        qs = qs.filter(
            Q(title__icontains=cd["q"])
            | Q(asset__name__icontains=cd["q"])
            | Q(responsible__icontains=cd["q"])
        )
    if cd.get("asset"):
        qs = qs.filter(asset=cd["asset"])
    if cd.get("responsible"):
        qs = qs.filter(responsible=cd["responsible"])
    # Status filtering is done in Python after fetching because next_due depends
    # on annotated last_performed_at — DB-side date math would be complex.
    # For list sizes typical in GMP (< 500 plans), this is acceptable.
    if cd.get("status"):
        qs = [p for p in qs if p.status == cd["status"]]
    return qs
