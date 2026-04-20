from datetime import date

from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Max, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.response import TemplateResponse
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView, View

from apps.assets.models import Asset

from apps.accounts.constants import Role
from apps.accounts.mixins import WriteAccessMixin
from apps.core.filters import build_toolbar_context
from apps.core.view_mixins import EmptyStateMixin

from .filter_defs import QUALIFICATION_FILTER_DIMENSIONS
from .forms import (
    QualificationCycleCreateForm,
    QualificationCycleFilterForm,
    QualificationCycleUpdateForm,
    SignatureForm,
)
from .models import QualificationCycle, QualificationSignature


def _cycle_qs():
    """Base queryset with last_signed_at annotation to avoid N+1."""
    return QualificationCycle.objects.select_related("asset").annotate(
        last_signed_at=Max("signatures__signed_at")
    )


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
    if cd.get("qual_type"):
        qs = qs.filter(qual_type=cd["qual_type"])
    if cd.get("asset"):
        qs = qs.filter(asset=cd["asset"])
    # Status filtering is done in Python after fetching because status depends
    # on the annotated last_signed_at — DB-side date math would be complex.
    if cd.get("status"):
        qs = [c for c in qs if c.status == cd["status"]]
    return qs


class QualificationCycleListView(EmptyStateMixin, LoginRequiredMixin, ListView):
    template_name = "qualification/cycle_list.html"
    context_object_name = "cycles"
    paginate_by = 25
    empty_icon = "qualification"
    empty_title = _("Noch keine Qualifizierungen")
    empty_desc = _("Starte einen IQ/OQ/PQ-Zyklus, um GMP-konforme Qualifizierung zu dokumentieren.")

    def get_queryset(self):
        return _apply_filters(_cycle_qs(), self._filter_form())

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        form = self._filter_form()
        ctx["filter_form"] = form
        ctx["can_write"] = self.request.user.has_role(Role.ADMIN, Role.USER)
        if ctx["can_write"]:
            ctx["empty_primary"] = {
                "label": _("Neuer Zyklus"), "url": reverse_lazy("qualification:create"), "icon": "+",
            }
        get_params = self.request.GET.copy()
        get_params.pop("page", None)
        ctx["filter_params"] = get_params.urlencode()
        ctx.update(build_toolbar_context(
            self.request, form, QUALIFICATION_FILTER_DIMENSIONS,
            search_placeholder=_("Bezeichnung, Anlage…"),
            hx_target="#cycle-list-body",
            inline_fields=["status", "qual_type", "asset"],
        ))
        return ctx

    def render_to_response(self, context, **kwargs):
        if self.request.headers.get("HX-Request") and not self.request.headers.get("HX-Boosted"):
            return TemplateResponse(
                self.request, "qualification/partials/_cycle_list_body.html", context
            )
        return super().render_to_response(context, **kwargs)

    def _filter_form(self):
        if not hasattr(self, "_cached_filter_form"):
            self._cached_filter_form = QualificationCycleFilterForm(self.request.GET or None)
        return self._cached_filter_form


class QualificationCycleDetailView(LoginRequiredMixin, DetailView):
    template_name = "qualification/cycle_detail.html"
    context_object_name = "cycle"

    def get_queryset(self):
        return _cycle_qs()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["can_write"] = self.request.user.has_role(Role.ADMIN, Role.USER)
        ctx["can_sign"] = self.request.user.has_role(Role.ADMIN)
        ctx["signatures"] = self.object.signatures.select_related("signed_by").order_by("-signed_at")
        ctx["sign_form"] = SignatureForm()
        return ctx


class QualificationCycleCreateView(LoginRequiredMixin, WriteAccessMixin, CreateView):
    form_class = QualificationCycleCreateForm
    template_name = "qualification/cycle_form.html"

    def get_success_url(self):
        return reverse("qualification:detail", kwargs={"pk": self.object.pk})

    def get_initial(self):
        initial = super().get_initial()
        asset_pk = self.request.GET.get("asset")
        if asset_pk:
            initial["asset"] = asset_pk
        return initial

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form_title"] = _("Neuer Qualifizierungszyklus")
        ctx["submit_label"] = _("Zyklus erstellen")
        return ctx

    def form_valid(self, form):
        messages.success(self.request, _("Qualifizierungszyklus wurde erfolgreich erstellt."))
        return super().form_valid(form)


class QualificationCycleUpdateView(LoginRequiredMixin, WriteAccessMixin, UpdateView):
    form_class = QualificationCycleUpdateForm
    template_name = "qualification/cycle_form.html"

    def get_queryset(self):
        return QualificationCycle.objects.select_related("asset")

    def get_success_url(self):
        return reverse("qualification:detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form_title"] = _("Qualifizierungszyklus bearbeiten")
        ctx["submit_label"] = _("Änderungen speichern")
        ctx["is_update"] = True
        return ctx

    def form_valid(self, form):
        messages.success(self.request, _("Qualifizierungszyklus wurde aktualisiert."))
        return super().form_valid(form)


class QualificationCycleDeleteView(LoginRequiredMixin, WriteAccessMixin, DeleteView):
    model = QualificationCycle
    template_name = "qualification/cycle_confirm_delete.html"
    context_object_name = "cycle"
    success_url = reverse_lazy("qualification:list")

    def form_valid(self, form):
        messages.success(self.request, _("Qualifizierungszyklus wurde gelöscht."))
        return super().form_valid(form)


class QualificationSignView(LoginRequiredMixin, View):
    """CFR 21 Part 11 electronic signature with re-authentication."""

    def post(self, request, pk):
        if not request.user.has_role(Role.ADMIN):
            raise PermissionDenied

        cycle = get_object_or_404(QualificationCycle, pk=pk)
        form = SignatureForm(request.POST)

        if not form.is_valid():
            return self._modal_error(request, cycle, form)

        # Re-authenticate
        user = authenticate(
            request,
            username=request.user.username,
            password=form.cleaned_data["password"],
        )
        if user is None:
            form.add_error("password", _("Passwort ist nicht korrekt."))
            return self._modal_error(request, cycle, form)

        # Capture client IP
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        ip_address = xff.split(",")[0].strip() if xff else request.META.get("REMOTE_ADDR")

        QualificationSignature.objects.create(
            cycle=cycle,
            signed_at=date.today(),
            signed_by=request.user,
            signed_by_username=request.user.get_username(),
            ip_address=ip_address,
            meaning=form.cleaned_data["meaning"],
            notes=form.cleaned_data["notes"],
        )
        messages.success(request, _("Qualifizierungszyklus wurde erfolgreich signiert."))
        detail_url = reverse("qualification:detail", kwargs={"pk": pk})
        if request.headers.get("HX-Request"):
            response = HttpResponse()
            response["HX-Redirect"] = detail_url
            return response
        return redirect(detail_url)

    def _modal_error(self, request, cycle, form):
        """Return the sign modal partial with validation errors (HTMX swap)."""
        return TemplateResponse(
            request,
            "qualification/partials/_sign_modal.html",
            {"cycle": cycle, "sign_form": form},
        )


@login_required
def asset_qualification_config(request, asset_pk):
    """Edit requalification_interval_years + pq_required for a single asset."""

    if not request.user.has_role(Role.ADMIN, Role.USER):
        raise PermissionDenied

    asset = get_object_or_404(Asset, pk=asset_pk)

    if request.method == "POST":
        try:
            years = int(request.POST.get("requalification_interval_years", ""))
        except (TypeError, ValueError):
            years = 0
        if 1 <= years <= 20:
            asset.requalification_interval_years = years
            asset.pq_required = bool(request.POST.get("pq_required"))
            asset.save(update_fields=["requalification_interval_years", "pq_required"])
            messages.success(request, _("Qualifizierungs-Intervall aktualisiert."))
            return redirect("assets:detail_qualification", pk=asset.pk)
        messages.error(request, _("Bitte einen gültigen Intervall zwischen 1 und 20 Jahren angeben."))

    return render(
        request,
        "qualification/config.html",
        {"asset": asset},
    )
