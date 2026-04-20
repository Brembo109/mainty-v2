from datetime import date, timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from apps.accounts.constants import Role
from apps.accounts.mixins import WriteAccessMixin
from apps.core.filters import build_toolbar_context
from apps.core.view_mixins import EmptyStateMixin

from .filter_defs import CONTRACT_FILTER_DIMENSIONS
from .forms import ContractFilterForm, ContractForm, ContractRenewalForm
from .models import Contract, ContractRenewal

_EXPIRY_WARNING_DAYS = getattr(settings, "CONTRACT_EXPIRY_WARNING_DAYS", 90)


class ContractListView(EmptyStateMixin, LoginRequiredMixin, ListView):
    model = Contract
    template_name = "contracts/contract_list.html"
    context_object_name = "contracts"
    paginate_by = 25
    empty_icon = "contract"
    empty_title = _("Noch keine Verträge")
    empty_desc = _("Lege Wartungs- oder Service-Verträge an, um Laufzeiten und Ablaufwarnungen zu verfolgen.")

    def get_queryset(self):
        return _apply_filters(
            Contract.objects.annotate(asset_count=Count("assets")),
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
                "label": _("Neuer Vertrag"), "url": reverse_lazy("contracts:create"), "icon": "+",
            }
        ctx.update(build_toolbar_context(
            self.request, form, CONTRACT_FILTER_DIMENSIONS,
            search_placeholder=_("Bezeichnung, Dienstleister, Nr.…"),
            hx_target="#contract-list-body",
            inline_fields=["status", "vendor", "asset"],
        ))
        return ctx

    def render_to_response(self, context, **kwargs):
        if self.request.headers.get("HX-Request") and not self.request.headers.get("HX-Boosted"):
            return TemplateResponse(
                self.request, "contracts/partials/_contract_list_body.html", context
            )
        return super().render_to_response(context, **kwargs)

    def _filter_form(self):
        if not hasattr(self, "_cached_filter_form"):
            self._cached_filter_form = ContractFilterForm(self.request.GET or None)
        return self._cached_filter_form


class ContractDetailView(LoginRequiredMixin, DetailView):
    model = Contract
    template_name = "contracts/contract_detail.html"
    context_object_name = "contract"

    def get_queryset(self):
        return Contract.objects.prefetch_related("assets")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["can_write"] = self.request.user.has_role(Role.ADMIN, Role.USER)
        ctx["renewals"] = self.object.renewals.select_related("renewed_by").all()
        return ctx


class ContractRenewView(LoginRequiredMixin, WriteAccessMixin, CreateView):
    model = ContractRenewal
    form_class = ContractRenewalForm
    template_name = "contracts/contract_renew.html"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.contract = Contract.objects.get(pk=kwargs["pk"])

    def get_initial(self):
        return {"previous_end_date": self.contract.end_date}

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["contract"] = self.contract
        return ctx

    def form_valid(self, form):
        renewal = form.save(commit=False)
        renewal.contract = self.contract
        renewal.previous_end_date = self.contract.end_date
        renewal.renewed_by = self.request.user
        renewal.save()
        self.contract.end_date = renewal.new_end_date
        self.contract.save()
        messages.success(self.request, _("Vertrag wurde erfolgreich verlängert."))
        return redirect(reverse("contracts:detail", kwargs={"pk": self.contract.pk}))


class ContractCreateView(LoginRequiredMixin, WriteAccessMixin, CreateView):
    model = Contract
    form_class = ContractForm
    template_name = "contracts/contract_form.html"
    success_url = reverse_lazy("contracts:list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form_title"] = _("Neuer Servicevertrag")
        ctx["submit_label"] = _("Vertrag erstellen")
        return ctx

    def form_valid(self, form):
        messages.success(self.request, _("Servicevertrag wurde erfolgreich erstellt."))
        return super().form_valid(form)


class ContractUpdateView(LoginRequiredMixin, WriteAccessMixin, UpdateView):
    model = Contract
    form_class = ContractForm
    template_name = "contracts/contract_form.html"
    success_url = reverse_lazy("contracts:list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form_title"] = _("Servicevertrag bearbeiten")
        ctx["submit_label"] = _("Änderungen speichern")
        return ctx

    def form_valid(self, form):
        messages.success(self.request, _("Servicevertrag wurde erfolgreich aktualisiert."))
        return super().form_valid(form)


class ContractDeleteView(LoginRequiredMixin, WriteAccessMixin, DeleteView):
    model = Contract
    template_name = "contracts/contract_confirm_delete.html"
    context_object_name = "contract"
    success_url = reverse_lazy("contracts:list")

    def form_valid(self, form):
        messages.success(self.request, _("Servicevertrag wurde gelöscht."))
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
            | Q(vendor__icontains=cd["q"])
            | Q(contract_number__icontains=cd["q"])
        )
    if cd.get("status"):
        today = date.today()
        warning_cutoff = today + timedelta(days=_EXPIRY_WARNING_DAYS)
        if cd["status"] == "active":
            qs = qs.filter(end_date__gt=warning_cutoff)
        elif cd["status"] == "expiring":
            qs = qs.filter(end_date__gte=today, end_date__lte=warning_cutoff)
        elif cd["status"] == "expired":
            qs = qs.filter(end_date__lt=today)
    if cd.get("vendor"):
        qs = qs.filter(vendor=cd["vendor"])
    if cd.get("asset"):
        qs = qs.filter(assets=cd["asset"])
    return qs
