from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.db.models import Max, Q
from django.shortcuts import get_object_or_404, render
from django.template.response import TemplateResponse
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from apps.accounts.constants import Role
from apps.accounts.mixins import WriteAccessMixin

from apps.audit.models import AuditLog
from apps.core.filters import build_toolbar_context
from apps.core.view_mixins import EmptyStateMixin

from .filter_defs import ASSET_FILTER_DIMENSIONS
from .forms import AssetFilterForm, AssetForm
from .models import Asset


TAB_SLUGS = ["overview", "maintenance", "qualification", "documents", "audit"]
TAB_LABELS = {
    "overview": _("Übersicht"),
    "maintenance": _("Wartung"),
    "qualification": _("Qualifizierung"),
    "documents": _("Dokumente"),
    "audit": _("Audit"),
}


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
# Detail-Shell tab views
# ---------------------------------------------------------------------------

def _shell_context(asset, active_tab, request):
    can_write = request.user.has_role(Role.ADMIN, Role.USER)
    actions = []
    if can_write:
        actions.append({
            "label": _("Bearbeiten"),
            "url": reverse("assets:update", args=[asset.pk]),
            "variant": "primary",
        })
    actions.append({
        "label": _("Zurück"),
        "url": reverse("assets:list"),
        "variant": "ghost",
    })
    subtitle_parts = []
    if asset.short_code:
        subtitle_parts.append(f"Kürzel {asset.short_code}")
    if asset.inventory_number:
        subtitle_parts.append(f"Inv. {asset.inventory_number}")
    return {
        "asset": asset,
        "active_tab": active_tab,
        "can_write": can_write,
        "title": asset.name,
        "subtitle": " · ".join(subtitle_parts),
        "status_dot": asset.status_dot,
        "meta_items": asset.meta_items(),
        "actions": actions,
        "tabs": [
            {
                "slug": slug,
                "label": TAB_LABELS[slug],
                "count": asset.tab_count(slug),
                "url": reverse(f"assets:detail_{slug}", args=[asset.pk]),
            }
            for slug in TAB_SLUGS
        ],
    }


def _is_htmx(request):
    return request.headers.get("HX-Request") and not request.headers.get("HX-Boosted")


def _render_tab(request, asset, active_tab, panel_template, extra_ctx):
    ctx = _shell_context(asset, active_tab, request)
    ctx.update(extra_ctx)
    ctx["panel_template"] = panel_template
    template = panel_template if _is_htmx(request) else "assets/asset_detail.html"
    return render(request, template, ctx)


def _asset_queryset():
    return Asset.objects.select_related("responsible", "deputy")


def _asset_audit_qs(asset):
    asset_ct = ContentType.objects.get_for_model(Asset)
    return AuditLog.objects.filter(
        content_type=asset_ct,
        object_id=str(asset.pk),
    ).select_related("actor", "content_type").order_by("-timestamp")


@login_required
def asset_detail(request, pk):
    return asset_overview(request, pk)


@login_required
def asset_overview(request, pk):
    asset = get_object_or_404(_asset_queryset(), pk=pk)
    recent = list(_asset_audit_qs(asset)[:5])
    return _render_tab(
        request, asset, "overview",
        "assets/_overview_panel.html",
        {"recent_activity": recent},
    )


@login_required
def asset_maintenance(request, pk):
    asset = get_object_or_404(_asset_queryset(), pk=pk)
    plans = (
        asset.maintenance_plans
        .annotate(last_performed_at=Max("records__performed_at"))
        .order_by("title")
    )
    return _render_tab(
        request, asset, "maintenance",
        "assets/_maintenance_panel.html",
        {"maintenance_plans": plans},
    )


@login_required
def asset_qualification(request, pk):
    from apps.qualification.constants import QualStage
    from apps.qualification.models import Qualification

    asset = get_object_or_404(_asset_queryset(), pk=pk)

    firsts = list(asset.qualifications.exclude(stage=QualStage.RQ))
    first_by_stage = {q.stage: q for q in firsts}
    first_qualifications = []
    for stage in QualStage.FIRST_STAGES:
        if stage == QualStage.PQ and not asset.pq_required and stage not in first_by_stage:
            continue
        q = first_by_stage.get(stage)
        if q is None:
            q = Qualification(asset=asset, stage=stage)
        first_qualifications.append(q)

    requalifications = list(
        asset.qualifications.filter(stage=QualStage.RQ).order_by("rq_cycle")
    )

    # Next planned RQ: last completed RQ + interval, or last completed first-stage
    # qualification + interval, or None if nothing is done.
    next_rq_date = None
    interval = asset.requalification_interval_years
    last_rq = next(
        (r for r in reversed(requalifications) if r.completed_on), None,
    )
    anchor_date = last_rq.completed_on if last_rq else None
    if anchor_date is None:
        anchor_q = max(
            (q.completed_on for q in firsts if q.completed_on),
            default=None,
        )
        anchor_date = anchor_q
    if anchor_date:
        next_rq_date = anchor_date.replace(year=anchor_date.year + interval)

    return _render_tab(
        request, asset, "qualification",
        "assets/_qualification_panel.html",
        {
            "first_qualifications": first_qualifications,
            "requalifications": requalifications,
            "next_rq_date": next_rq_date,
        },
    )


@login_required
def asset_documents(request, pk):
    asset = get_object_or_404(_asset_queryset(), pk=pk)
    doc_links = [
        (asset.logbook_ref, asset.logbook_url, _("Logbuch (LOG)")),
        (asset.bal_ref, asset.bal_url, _("Bedienungsanleitung (BAL)")),
    ]
    documents = [
        {"ref": ref, "url": url, "label": label}
        for ref, url, label in doc_links
        if ref
    ]
    return _render_tab(
        request, asset, "documents",
        "assets/_documents_panel.html",
        {"asset_documents": documents},
    )


@login_required
def asset_audit(request, pk):
    asset = get_object_or_404(_asset_queryset(), pk=pk)
    events = list(_asset_audit_qs(asset)[:100])
    total = _asset_audit_qs(asset).count()
    return _render_tab(
        request, asset, "audit",
        "assets/_audit_panel.html",
        {"audit_events": events, "audit_total": total},
    )


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
