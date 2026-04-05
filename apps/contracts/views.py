from datetime import date, timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.template.response import TemplateResponse
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from apps.accounts.constants import Role
from apps.accounts.mixins import WriteAccessMixin

from .forms import ContractFilterForm, ContractForm
from .models import Contract

_EXPIRY_WARNING_DAYS = getattr(settings, "CONTRACT_EXPIRY_WARNING_DAYS", 90)


class ContractListView(LoginRequiredMixin, ListView):
    model = Contract
    template_name = "contracts/contract_list.html"
    context_object_name = "contracts"
    paginate_by = 25

    def get_queryset(self):
        return _apply_filters(
            Contract.objects.annotate(asset_count=Count("assets")),
            self._filter_form(),
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["filter_form"] = self._filter_form()
        get_params = self.request.GET.copy()
        get_params.pop("page", None)
        ctx["filter_params"] = get_params.urlencode()
        ctx["can_write"] = self.request.user.has_role(Role.ADMIN, Role.USER)
        return ctx

    def render_to_response(self, context, **kwargs):
        if self.request.headers.get("HX-Request") and not self.request.headers.get("HX-Boosted"):
            return TemplateResponse(
                self.request, "contracts/partials/_contract_table.html", context
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
        return ctx


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
    return qs
