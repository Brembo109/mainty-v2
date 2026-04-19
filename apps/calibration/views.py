from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView, View

from apps.accounts.constants import Role
from apps.accounts.mixins import RoleRequiredMixin, WriteAccessMixin
from apps.core.filters import build_toolbar_context

from .filter_defs import CALIBRATION_FILTER_DIMENSIONS
from .forms import (
    CalibrationRecordCompleteForm,
    CalibrationRecordForm,
    TestEquipmentFilterForm,
    TestEquipmentForm,
)
from .models import CalibrationRecord, TestEquipment


class TestEquipmentListView(LoginRequiredMixin, ListView):
    model = TestEquipment
    template_name = "calibration/equipment_list.html"
    context_object_name = "equipment_list"
    paginate_by = 25

    def get_queryset(self):
        return _apply_filters(
            TestEquipment.objects.select_related("asset", "responsible").prefetch_related("records"),
            self._filter_form(),
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        form = self._filter_form()
        ctx["filter_form"] = form
        ctx["can_write"] = self.request.user.has_role(Role.ADMIN, Role.USER)
        get_params = self.request.GET.copy()
        get_params.pop("page", None)
        ctx["filter_params"] = get_params.urlencode()
        ctx.update(build_toolbar_context(
            self.request, form, CALIBRATION_FILTER_DIMENSIONS,
            search_placeholder=_("Bezeichnung, Seriennr., Hersteller…"),
            hx_target="#equipment-list-body",
            inline_fields=["status", "location", "responsible"],
        ))
        return ctx

    def render_to_response(self, context, **kwargs):
        if self.request.headers.get("HX-Request") and not self.request.headers.get("HX-Boosted"):
            return TemplateResponse(
                self.request, "calibration/partials/_equipment_list_body.html", context
            )
        return super().render_to_response(context, **kwargs)

    def _filter_form(self):
        if not hasattr(self, "_cached_filter_form"):
            self._cached_filter_form = TestEquipmentFilterForm(self.request.GET or None)
        return self._cached_filter_form


class TestEquipmentDetailView(LoginRequiredMixin, DetailView):
    model = TestEquipment
    template_name = "calibration/equipment_detail.html"
    context_object_name = "equipment"

    def get_queryset(self):
        return TestEquipment.objects.select_related("asset", "responsible")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["can_write"] = self.request.user.has_role(Role.ADMIN, Role.USER)
        ctx["can_admin"] = self.request.user.has_role(Role.ADMIN)
        ctx["records"] = self.object.records.select_related(
            "performed_by"
        ).order_by("-calibrated_at", "-sent_at", "-created_at")
        ctx["record_form"] = CalibrationRecordForm(
            initial={"performed_by": self.request.user}
        )
        open_record = self.object.open_record
        ctx["open_record"] = open_record
        return ctx


class TestEquipmentCreateView(LoginRequiredMixin, WriteAccessMixin, CreateView):
    model = TestEquipment
    form_class = TestEquipmentForm
    template_name = "calibration/equipment_form.html"

    def get_success_url(self):
        return reverse("calibration:detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form_title"] = _("Neues Prüfmittel")
        ctx["submit_label"] = _("Prüfmittel erstellen")
        return ctx

    def form_valid(self, form):
        messages.success(self.request, _("Prüfmittel wurde erfolgreich erstellt."))
        return super().form_valid(form)


class TestEquipmentUpdateView(LoginRequiredMixin, WriteAccessMixin, UpdateView):
    model = TestEquipment
    form_class = TestEquipmentForm
    template_name = "calibration/equipment_form.html"

    def get_success_url(self):
        return reverse("calibration:detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form_title"] = _("Prüfmittel bearbeiten")
        ctx["submit_label"] = _("Änderungen speichern")
        return ctx

    def form_valid(self, form):
        messages.success(self.request, _("Prüfmittel wurde aktualisiert."))
        return super().form_valid(form)


class TestEquipmentDeleteView(LoginRequiredMixin, WriteAccessMixin, DeleteView):
    model = TestEquipment
    template_name = "calibration/equipment_confirm_delete.html"
    context_object_name = "equipment"
    success_url = reverse_lazy("calibration:list")

    def form_valid(self, form):
        messages.success(self.request, _("Prüfmittel wurde gelöscht."))
        return super().form_valid(form)


class CalibrationRecordCreateView(LoginRequiredMixin, WriteAccessMixin, View):
    """Create a calibration record for a piece of equipment. Redirects back to detail."""

    def post(self, request, pk):
        equipment = get_object_or_404(
            TestEquipment.objects.select_related("asset", "responsible"), pk=pk
        )
        form = CalibrationRecordForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            record.equipment = equipment
            record.save()
            messages.success(request, _("Kalibrierungseintrag wurde erfasst."))
            return redirect(reverse("calibration:detail", kwargs={"pk": pk}))
        # Re-render detail with bound form so field-level errors are visible
        ctx = {
            "equipment": equipment,
            "can_write": request.user.has_role(Role.ADMIN, Role.USER),
            "records": equipment.records.select_related("performed_by").order_by(
                "-calibrated_at", "-sent_at", "-created_at"
            ),
            "record_form": form,
            "open_record": equipment.open_record,
        }
        return TemplateResponse(request, "calibration/equipment_detail.html", ctx)


class CalibrationRecordUpdateView(LoginRequiredMixin, RoleRequiredMixin, UpdateView):
    model = CalibrationRecord
    form_class = CalibrationRecordForm
    template_name = "calibration/record_form.html"
    context_object_name = "record"
    required_role = Role.ADMIN

    def get_object(self, queryset=None):
        return get_object_or_404(
            CalibrationRecord.objects.select_related("equipment"),
            pk=self.kwargs["record_pk"],
            equipment_id=self.kwargs["pk"],
        )

    def get_success_url(self):
        return reverse("calibration:detail", kwargs={"pk": self.kwargs["pk"]})

    def form_valid(self, form):
        messages.success(self.request, _("Kalibrierungseintrag wurde aktualisiert."))
        return super().form_valid(form)


class CalibrationRecordDeleteView(LoginRequiredMixin, RoleRequiredMixin, DeleteView):
    model = CalibrationRecord
    template_name = "calibration/record_confirm_delete.html"
    context_object_name = "record"
    required_role = Role.ADMIN

    def get_object(self, queryset=None):
        return get_object_or_404(
            CalibrationRecord.objects.select_related("equipment"),
            pk=self.kwargs["record_pk"],
            equipment_id=self.kwargs["pk"],
        )

    def get_success_url(self):
        return reverse("calibration:detail", kwargs={"pk": self.kwargs["pk"]})

    def form_valid(self, form):
        messages.success(self.request, _("Kalibrierungseintrag wurde gelöscht."))
        return super().form_valid(form)


class CalibrationRecordCompleteView(LoginRequiredMixin, WriteAccessMixin, View):
    """Complete an open AT_LAB record by adding the calibration result."""

    def _get_record(self, record_pk):
        return get_object_or_404(
            CalibrationRecord.objects.select_related("equipment"),
            pk=record_pk,
            sent_at__isnull=False,
            calibrated_at__isnull=True,
        )

    def get(self, request, record_pk):
        record = self._get_record(record_pk)
        form = CalibrationRecordCompleteForm(instance=record)
        return TemplateResponse(request, "calibration/record_complete_form.html", {
            "form": form,
            "record": record,
            "equipment": record.equipment,
        })

    def post(self, request, record_pk):
        record = self._get_record(record_pk)
        form = CalibrationRecordCompleteForm(request.POST, instance=record)
        if form.is_valid():
            form.save()
            messages.success(request, _("Kalibrierungsergebnis wurde erfolgreich eingetragen."))
            return redirect(reverse("calibration:detail", kwargs={"pk": record.equipment.pk}))
        return TemplateResponse(request, "calibration/record_complete_form.html", {
            "form": form,
            "record": record,
            "equipment": record.equipment,
        })


# ---------------------------------------------------------------------------
# Shared filter logic
# ---------------------------------------------------------------------------

def _apply_filters(qs, form):
    if not form.is_valid():
        return qs
    cd = form.cleaned_data
    if cd.get("q"):
        qs = qs.filter(
            Q(name__icontains=cd["q"])
            | Q(serial_number__icontains=cd["q"])
            | Q(manufacturer__icontains=cd["q"])
            | Q(asset__name__icontains=cd["q"])
        )
    if cd.get("location"):
        qs = qs.filter(location=cd["location"])
    if cd.get("responsible"):
        qs = qs.filter(responsible=cd["responsible"])
    # Status filtering in Python — status is a computed property depending on DB records.
    # Acceptable for GMP list sizes (< 500 items).
    if cd.get("status"):
        qs = [e for e in qs if e.status == cd["status"]]
    return qs
