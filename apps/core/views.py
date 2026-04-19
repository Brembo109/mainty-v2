import calendar as _calendar
from datetime import date, timedelta

from django.contrib import messages
from django.core.mail import send_mail
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
from apps.core.calendar_utils import build_month_events, build_day_events, ALL_TYPES
from apps.core.forms import SiteConfigForm
from apps.core.models import SiteConfig
from apps.contracts.models import Contract
from apps.maintenance.models import MaintenancePlan
from apps.qualification.models import QualificationCycle
from apps.tasks.models import Task

def health(request):
    return JsonResponse({"status": "ok"})


@login_required
def index(request):
    today = date.today()
    config = SiteConfig.get()
    contract_warning = today + timedelta(days=config.contract_expiry_warning_days)

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
    open_tasks_total = Task.objects.exclude(status="done").count()
    tasks_overdue_total = Task.objects.exclude(status="done").filter(due_date__lt=today).count()

    # ── 30-day timeline ──────────────────────────────────────────────────
    _WEEKDAYS_DE = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
    timeline_raw = []

    for plan in maint_plans:
        if plan.next_due:
            delta = (plan.next_due - today).days
            if delta <= 30:
                timeline_raw.append({
                    "day": delta,
                    "type": "Wartung",
                    "type_key": "maint",
                    "pk": plan.pk,
                    "title": plan.title,
                    "asset": plan.asset.name,
                    "status": "danger" if delta < 0 else ("warn" if delta <= 7 else "info"),
                })

    for cycle in qual_cycles:
        if cycle.next_due:
            delta = (cycle.next_due - today).days
            if delta <= 30:
                timeline_raw.append({
                    "day": delta,
                    "type": "Qual.",
                    "type_key": "qual",
                    "pk": cycle.pk,
                    "title": cycle.title,
                    "asset": cycle.asset.name,
                    "status": "danger" if delta < 0 else ("warn" if delta <= 7 else "info"),
                })

    for contract in Contract.objects.filter(
        end_date__gte=today - timedelta(days=7),
        end_date__lte=today + timedelta(days=30),
    ).order_by("end_date"):
        delta = (contract.end_date - today).days
        timeline_raw.append({
            "day": delta,
            "type": "Vertrag",
            "type_key": "contract",
            "pk": contract.pk,
            "title": contract.title,
            "asset": "—",
            "status": "danger" if delta < 0 else ("warn" if delta <= 14 else "info"),
        })

    for task in (
        Task.objects.exclude(status="done")
        .filter(due_date__isnull=False, due_date__lte=today + timedelta(days=30))
        .select_related("asset")
        .order_by("due_date")
    ):
        delta = (task.due_date - today).days
        timeline_raw.append({
            "day": delta,
            "type": "Aufgabe",
            "type_key": "task",
            "pk": task.pk,
            "title": task.title,
            "asset": task.asset.name if task.asset else "—",
            "status": "danger" if delta < 0 else ("warn" if delta <= 3 else "info"),
        })

    timeline_raw.sort(key=lambda e: e["day"])

    timeline_days = []
    for i in range(30):
        d = today + timedelta(days=i)
        day_events = [e for e in timeline_raw if e["day"] == i]
        worst = None
        for e in day_events:
            if e["status"] == "danger":
                worst = "danger"
                break
            elif e["status"] == "warn" and worst != "danger":
                worst = "warn"
            elif worst is None:
                worst = "info"
        dow = d.weekday()
        timeline_days.append({
            "date": d,
            "day_num": d.day,
            "weekday": _WEEKDAYS_DE[dow],
            "is_today": i == 0,
            "is_weekend": dow >= 5,
            "dot_status": worst,
            "event_count": len(day_events),
        })

    overdue_events   = [e for e in timeline_raw if e["day"] < 0]
    today_events     = [e for e in timeline_raw if e["day"] == 0]
    thisweek_events  = [e for e in timeline_raw if 1 <= e["day"] <= 4]
    nextweek_events  = [e for e in timeline_raw if 5 <= e["day"] <= 11]
    later_events     = [e for e in timeline_raw if e["day"] >= 12]

    timeline_total         = len(timeline_raw)
    timeline_overdue_count = len(overdue_events)
    timeline_thisweek_count = len(today_events) + len(thisweek_events)

    total_items = len(maint_plans) + len(qual_cycles)
    overdue_items = maint_overdue + qual_overdue
    gmp_compliance = (
        round((total_items - overdue_items) / total_items * 100, 1) if total_items > 0 else 100.0
    )

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
        "open_tasks_total": open_tasks_total,
        "tasks_overdue_total": tasks_overdue_total,
        # timeline
        "timeline_days": timeline_days,
        "timeline_total": timeline_total,
        "timeline_overdue_count": timeline_overdue_count,
        "timeline_thisweek_count": timeline_thisweek_count,
        "overdue_events": overdue_events,
        "today_events": today_events,
        "thisweek_events": thisweek_events,
        "nextweek_events": nextweek_events,
        "later_events": later_events,
        "gmp_compliance": gmp_compliance,
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
            send_mail(
                subject=_("mainty — Test-E-Mail"),
                message=_("Die E-Mail-Konfiguration funktioniert korrekt."),
                from_email=config.email_from,
                recipient_list=[request.user.email],
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


def _parse_month(month_str):
    """Parse 'YYYY-MM' string; fall back to today's month."""
    if month_str:
        try:
            year, month = month_str.split("-")
            year, month = int(year), int(month)
            date(year, month, 1)  # validate range
            return year, month
        except (ValueError, AttributeError):
            pass
    today = date.today()
    return today.year, today.month


class CalendarView(LoginRequiredMixin, View):
    def get(self, request):
        year, month = _parse_month(request.GET.get("month"))
        types = request.GET.getlist("types") or ALL_TYPES

        first_day = date(year, month, 1)
        cal = _calendar.Calendar(firstweekday=0)  # Monday first
        weeks = cal.monthdatescalendar(year, month)
        events_by_date = build_month_events(year, month, types)

        # Build dots dict: {date: {type: dot_color}} — unique type per day
        dots_by_date = {}
        for d, evts in events_by_date.items():
            seen = {}
            for e in evts:
                if e["type"] not in seen:
                    seen[e["type"]] = e["dot_color"]
            dots_by_date[d] = seen

        today = date.today()
        # Prev/next month strings for HTMX nav links
        if month == 1:
            prev_month = f"{year - 1}-12"
        else:
            prev_month = f"{year}-{month - 1:02d}"
        if month == 12:
            next_month = f"{year + 1}-01"
        else:
            next_month = f"{year}-{month + 1:02d}"

        ctx = {
            "year": year,
            "month": month,
            "first_day": first_day,
            "weeks": weeks,
            "events_by_date": events_by_date,
            "dots_by_date": dots_by_date,
            "today": today,
            "selected_types": types,
            "all_types": ALL_TYPES,
            "prev_month": prev_month,
            "next_month": next_month,
            "weekday_names": ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"],
            "filter_types": [
                ("maintenance", "Wartung", "bg-status-danger"),
                ("qualification", "Qualifizierung", "bg-status-warning"),
                ("task", "Aufgaben", "bg-status-success"),
                ("calibration", "Kalibrierung", "bg-blue-400"),
                ("contract", "Verträge", "bg-purple-400"),
            ],
        }

        if request.headers.get("HX-Request"):
            return render(request, "core/partials/_calendar_grid.html", ctx)
        return render(request, "core/calendar.html", ctx)


class CalendarDayView(LoginRequiredMixin, View):
    def get(self, request):
        date_str = request.GET.get("date", "")
        types = request.GET.getlist("types") or ALL_TYPES
        selected_date = None
        day_events = []

        if date_str:
            try:
                selected_date = date.fromisoformat(date_str)
                day_events = build_day_events(selected_date, types)
            except ValueError:
                pass

        return render(request, "core/partials/_calendar_day.html", {
            "selected_date": selected_date,
            "day_events": day_events,
        })
