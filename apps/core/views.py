from datetime import date, timedelta

from django.conf import settings
from django.contrib import messages
from django.core.mail import get_connection, send_mail
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Max
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _
from django.views import View

from apps.accounts.constants import Role
from apps.accounts.mixins import RoleRequiredMixin
from apps.assets.models import Asset
from apps.core.forms import SiteConfigForm
from apps.core.models import SiteConfig
from apps.contracts.models import Contract
from apps.maintenance.models import MaintenancePlan
from apps.qualification.models import QualificationCycle
from apps.tasks.models import Task

_CONTRACT_WARNING_DAYS = getattr(settings, "CONTRACT_EXPIRY_WARNING_DAYS", 90)


def health(request):
    return JsonResponse({"status": "ok"})


@login_required
def index(request):
    today = date.today()
    contract_warning = today + timedelta(days=_CONTRACT_WARNING_DAYS)

    # ── Assets ──────────────────────────────────────────────────────────
    asset_count = Asset.objects.count()

    # ── Contracts (DB-side filtering, no Python iteration needed) ────────
    contracts_expired = Contract.objects.filter(end_date__lt=today).count()
    contracts_expiring = Contract.objects.filter(
        end_date__gte=today, end_date__lte=contract_warning
    ).count()
    contracts_active = Contract.objects.filter(end_date__gt=contract_warning).count()

    # ── Maintenance (status is a Python property — fetch all, iterate once) ─
    maint_plans = list(
        MaintenancePlan.objects.select_related("asset")
        .annotate(last_performed_at=Max("records__performed_at"))
    )
    maint_overdue = sum(1 for p in maint_plans if p.status == "overdue")
    maint_due_soon = sum(1 for p in maint_plans if p.status == "due_soon")
    maint_ok = sum(1 for p in maint_plans if p.status == "ok")
    critical_maintenance = sorted(
        [p for p in maint_plans if p.status in ("overdue", "due_soon")],
        key=lambda p: p.next_due,
    )[:8]

    # ── Qualification (same pattern) ─────────────────────────────────────
    qual_cycles = list(
        QualificationCycle.objects.select_related("asset")
        .annotate(last_signed_at=Max("signatures__signed_at"))
    )
    qual_overdue = sum(1 for c in qual_cycles if c.status == "overdue")
    qual_due_soon = sum(1 for c in qual_cycles if c.status == "due_soon")
    qual_never = sum(1 for c in qual_cycles if c.status == "never_signed")
    critical_qualification = sorted(
        [c for c in qual_cycles if c.status in ("overdue", "due_soon", "never_signed")],
        key=lambda c: c.next_due,
    )[:8]

    # ── Expiring contracts for sidebar widget ────────────────────────────
    expiring_contracts = (
        Contract.objects.filter(end_date__gte=today, end_date__lte=contract_warning)
        .order_by("end_date")[:6]
    )

    # ── Open tasks ───────────────────────────────────────────────────────
    open_tasks = list(
        Task.objects.select_related("asset", "assigned_to")
        .exclude(status="done")
        .order_by("-priority", "due_date")[:8]
    )
    tasks_overdue = sum(1 for t in open_tasks if t.is_overdue)

    return render(request, "core/index.html", {
        "asset_count": asset_count,
        "contracts_active": contracts_active,
        "contracts_expiring": contracts_expiring,
        "contracts_expired": contracts_expired,
        "maint_overdue": maint_overdue,
        "maint_due_soon": maint_due_soon,
        "maint_ok": maint_ok,
        "qual_overdue": qual_overdue,
        "qual_due_soon": qual_due_soon,
        "qual_never": qual_never,
        "critical_maintenance": critical_maintenance,
        "critical_qualification": critical_qualification,
        "expiring_contracts": expiring_contracts,
        "open_tasks": open_tasks,
        "tasks_overdue": tasks_overdue,
    })


class SettingsView(LoginRequiredMixin, RoleRequiredMixin, View):
    required_role = Role.ADMIN
    template_name = "core/settings.html"

    def get(self, request):
        config = SiteConfig.get()
        form = SiteConfigForm(instance=config)
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        config = SiteConfig.get()
        form = SiteConfigForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, _("Einstellungen wurden gespeichert."))
            return redirect("core:settings")
        return render(request, self.template_name, {"form": form})


class SendTestEmailView(LoginRequiredMixin, RoleRequiredMixin, View):
    required_role = Role.ADMIN

    def post(self, request):
        if not request.user.email:
            messages.error(request, _("Diesem Benutzer ist keine E-Mail-Adresse zugeordnet."))
            return redirect("core:settings")

        config = SiteConfig.get()
        try:
            connection = get_connection(
                host=config.email_host,
                port=config.email_port,
                username=config.email_host_user,
                password=config.email_host_password,
                use_tls=config.email_use_tls,
            )
            send_mail(
                subject=_("mainty — Test-E-Mail"),
                message=_("Die E-Mail-Konfiguration funktioniert korrekt."),
                from_email=config.email_from,
                recipient_list=[request.user.email],
                connection=connection,
            )
            messages.success(
                request,
                _("Test-E-Mail wurde gesendet an %(email)s.") % {"email": request.user.email},
            )
        except Exception as exc:
            messages.error(
                request,
                _("Fehler beim Senden: %(error)s") % {"error": str(exc)},
            )
        return redirect("core:settings")
