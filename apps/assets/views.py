from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Max, Q
from django.template.response import TemplateResponse
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from apps.accounts.constants import Role
from apps.accounts.mixins import WriteAccessMixin

from apps.core.filters import build_toolbar_context
from apps.core.view_mixins import EmptyStateMixin

from .filter_defs import ASSET_FILTER_DIMENSIONS
from .forms import AssetFilterForm, AssetForm
from .models import Asset


class AssetListView(EmptyStateMixin, LoginRequiredMixin, ListView):
    model = Asset
    template_name = "assets/asset_list.html"
    context_object_name = "assets"
    paginate_by = 25
    empty_icon = "asset"
    empty_title = _("Noch keine Anlagen")
    empty_desc = _("Lege deine erste Anlage an, um Wartung, Qualifizierung und Verträge zu verfolgen.")

    def get_queryset(self):
        return _apply_filters(
            Asset.objects.select_related("responsible", "deputy").all(),
            self._filter_form(),
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        form = self._filter_form()
        ctx["filter_form"] = form
        get_params = self.request.GET.copy()
        get_params.pop("page", None)
        ctx["filter_params"] = get_params.urlencode()
        ctx["can_write"] = self.request.user.has_role(Role.ADMIN, Role.USER)
        if ctx["can_write"]:
            ctx["empty_primary"] = {
                "label": _("Neue Anlage"), "url": reverse_lazy("assets:create"), "icon": "+",
            }
        ctx.update(build_toolbar_context(
            self.request, form, ASSET_FILTER_DIMENSIONS,
            search_placeholder=_("Anlage, Seriennr., Hersteller…"),
            hx_target="#asset-list-body",
            inline_fields=[
                "status", "location", "department", "responsible",
                "manufacturer", "has_contract",
            ],
        ))
        return ctx

    def render_to_response(self, context, **kwargs):
        if self.request.headers.get("HX-Request") and not self.request.headers.get("HX-Boosted"):
            return TemplateResponse(
                self.request, "assets/partials/_asset_list_body.html", context
            )
        return super().render_to_response(context, **kwargs)

    def _filter_form(self):
        if not hasattr(self, "_cached_filter_form"):
            self._cached_filter_form = AssetFilterForm(self.request.GET or None)
        return self._cached_filter_form


class AssetDetailView(LoginRequiredMixin, DetailView):
    model = Asset
    template_name = "assets/asset_detail.html"
    context_object_name = "asset"

    def get_queryset(self):
        return super().get_queryset().select_related("responsible", "deputy")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["can_write"] = self.request.user.has_role(Role.ADMIN, Role.USER)
        ctx["contracts"] = self.object.contracts.order_by("end_date")
        ctx["maintenance_plans"] = (
            self.object.maintenance_plans
            .annotate(last_performed_at=Max("records__performed_at"))
            .order_by("title")
        )
        ctx["qualification_cycles"] = (
            self.object.qualification_cycles
            .annotate(last_signed_at=Max("signatures__signed_at"))
            .order_by("qual_type", "title")
        )
        ctx["asset_tasks"] = (
            self.object.tasks
            .select_related("assigned_to")
            .exclude(status="done")
            .order_by("status", "-priority", "due_date")
        )
        return ctx


class AssetCreateView(LoginRequiredMixin, WriteAccessMixin, CreateView):
    model = Asset
    form_class = AssetForm
    template_name = "assets/asset_form.html"
    success_url = reverse_lazy("assets:list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form_title"] = _("Neue Anlage")
        ctx["submit_label"] = _("Anlage erstellen")
        return ctx

    def form_valid(self, form):
        messages.success(self.request, _("Anlage wurde erfolgreich erstellt."))
        return super().form_valid(form)


class AssetUpdateView(LoginRequiredMixin, WriteAccessMixin, UpdateView):
    model = Asset
    form_class = AssetForm
    template_name = "assets/asset_form.html"
    success_url = reverse_lazy("assets:list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form_title"] = _("Anlage bearbeiten")
        ctx["submit_label"] = _("Änderungen speichern")
        return ctx

    def form_valid(self, form):
        messages.success(self.request, _("Anlage wurde erfolgreich aktualisiert."))
        return super().form_valid(form)


class AssetDeleteView(LoginRequiredMixin, WriteAccessMixin, DeleteView):
    model = Asset
    template_name = "assets/asset_confirm_delete.html"
    context_object_name = "asset"
    success_url = reverse_lazy("assets:list")

    def form_valid(self, form):
        messages.success(self.request, _("Anlage wurde gelöscht."))
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
            Q(name__icontains=cd["q"])
            | Q(serial_number__icontains=cd["q"])
            | Q(manufacturer__icontains=cd["q"])
        )
    if cd.get("status"):
        qs = qs.filter(status=cd["status"])
    if cd.get("location"):
        qs = qs.filter(location__icontains=cd["location"])
    if cd.get("department"):
        qs = qs.filter(department=cd["department"])
    if cd.get("responsible"):
        qs = qs.filter(responsible=cd["responsible"])
    if cd.get("manufacturer"):
        qs = qs.filter(manufacturer=cd["manufacturer"])
    if cd.get("has_contract") == "yes":
        qs = qs.filter(contracts__isnull=False).distinct()
    elif cd.get("has_contract") == "no":
        qs = qs.filter(contracts__isnull=True)
    return qs
