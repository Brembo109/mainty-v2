"""Management command: send daily GMP reminder emails.

Usage:
    python manage.py send_reminders
    python manage.py send_reminders --force   # bypass once-per-day guard

Schedule via cron (example — runs at 07:00 every day):
    0 7 * * * /app/.venv/bin/python /app/manage.py send_reminders >> /var/log/mainty/reminders.log 2>&1

Or via systemd timer (see docs/reminders-systemd.md).
"""

from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives, get_connection
from django.core.management.base import BaseCommand
from django.db.models import Max
from django.template.loader import render_to_string

from apps.contracts.models import Contract
from apps.core.models import SiteConfig
from apps.maintenance.models import MaintenancePlan
from apps.qualification.models import QualificationCycle
from apps.tasks.models import Task

User = get_user_model()


class Command(BaseCommand):
    help = "Send daily GMP reminder emails to Admin and User role accounts."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Send even if a reminder was already sent today.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print what would be sent without sending emails.",
        )

    def handle(self, *args, **options):
        from apps.core.models import ReminderLog

        config = SiteConfig.get()
        today = date.today()
        force = options["force"]
        dry_run = options["dry_run"]

        # ── Once-per-day guard ────────────────────────────────────────────
        if not force and not dry_run:
            already_sent = ReminderLog.objects.filter(sent_at__date=today).exists()
            if already_sent:
                self.stdout.write(
                    self.style.WARNING(f"Reminder already sent today ({today}). Use --force to override.")
                )
                return

        # ── Build item lists ──────────────────────────────────────────────
        contract_warning = today + timedelta(days=config.contract_expiry_warning_days)
        items = self._collect_items(today, contract_warning)
        total = sum(len(v) for v in items.values())

        if total == 0:
            self.stdout.write(self.style.SUCCESS("No action items found — no email sent."))
            if not dry_run:
                ReminderLog.objects.create(
                    recipient_count=0,
                    summary={"items_found": 0},
                )
            return

        # ── Collect recipients (Admin + User roles) ───────────────────────
        recipients = list(
            User.objects.filter(
                groups__name__in=["Admin", "User"],
                is_active=True,
                email__contains="@",
            ).values_list("email", flat=True).distinct()
        )

        if not recipients:
            self.stdout.write(self.style.WARNING("No recipients with email addresses found."))
            return

        if dry_run:
            self._print_dry_run(items, recipients)
            return

        # ── Render and send ───────────────────────────────────────────────
        context = {
            "today": today,
            "site_url": config.site_url,
            **items,
        }
        html_body = render_to_string("emails/reminder.html", context)
        text_body = self._text_body(items, config.site_url)

        connection = get_connection(
            host=config.email_host,
            port=config.email_port,
            username=config.email_host_user,
            password=config.email_host_password,
            use_tls=config.email_use_tls,
        )
        msg = EmailMultiAlternatives(
            subject=config.reminder_email_subject,
            body=text_body,
            from_email=config.email_from,
            to=recipients,
            connection=connection,
        )
        msg.attach_alternative(html_body, "text/html")
        msg.send()

        # ── Log ───────────────────────────────────────────────────────────
        summary = {k: [str(i) for i in v] for k, v in items.items()}
        summary["items_found"] = total
        ReminderLog.objects.create(
            recipient_count=len(recipients),
            summary=summary,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Reminder sent to {len(recipients)} recipient(s) with {total} action item(s)."
            )
        )

    # ── Helpers ───────────────────────────────────────────────────────────

    def _collect_items(self, today, contract_warning):
        # Contracts — DB-side
        contracts_expiring = list(
            Contract.objects.filter(end_date__gte=today, end_date__lte=contract_warning)
            .order_by("end_date")
        )
        contracts_expired = list(
            Contract.objects.filter(end_date__lt=today).order_by("end_date")
        )

        # Maintenance — Python-side (status is a property)
        maint_plans = list(
            MaintenancePlan.objects.select_related("asset")
            .annotate(last_performed_at=Max("records__performed_at"))
        )
        maint_overdue = [p for p in maint_plans if p.status == "overdue"]
        maint_due_soon = [p for p in maint_plans if p.status == "due_soon"]

        # Qualification — Python-side
        qual_cycles = list(
            QualificationCycle.objects.select_related("asset")
            .annotate(last_signed_at=Max("signatures__signed_at"))
        )
        qual_overdue = [c for c in qual_cycles if c.status == "overdue"]
        qual_due_soon = [c for c in qual_cycles if c.status == "due_soon"]
        qual_never = [c for c in qual_cycles if c.status == "never_signed"]

        # Tasks — DB-side (status is a stored field)
        tasks_overdue = list(
            Task.objects.select_related("asset", "assigned_to")
            .exclude(status="done")
            .filter(due_date__lt=today)
            .order_by("due_date")
        )

        return {
            "contracts_expiring": contracts_expiring,
            "contracts_expired": contracts_expired,
            "maint_overdue": maint_overdue,
            "maint_due_soon": maint_due_soon,
            "qual_overdue": qual_overdue,
            "qual_due_soon": qual_due_soon,
            "qual_never": qual_never,
            "tasks_overdue": tasks_overdue,
        }

    def _print_dry_run(self, items, recipients):
        self.stdout.write(self.style.MIGRATE_HEADING("=== DRY RUN ==="))
        self.stdout.write(f"Recipients: {', '.join(recipients)}")
        for key, objs in items.items():
            if objs:
                self.stdout.write(f"\n{key} ({len(objs)}):")
                for obj in objs:
                    self.stdout.write(f"  - {obj}")

    def _text_body(self, items, site_url):
        lines = ["GMP-Erinnerung — Handlungsbedarf", "=" * 40, ""]
        for key, objs in items.items():
            if objs:
                lines.append(f"{key.upper()} ({len(objs)})")
                for obj in objs:
                    lines.append(f"  - {obj}")
                lines.append("")
        lines.append(f"Details: {site_url}")
        return "\n".join(lines)
