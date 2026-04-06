from datetime import date, timedelta

from django.db.models import Max

from apps.contracts.models import Contract
from apps.maintenance.constants import MaintenanceStatus
from apps.maintenance.models import MaintenancePlan
from apps.qualification.constants import QualStatus
from apps.qualification.models import QualificationCycle
from apps.tasks.models import Task

from .constants import Category


def collect_critical_items(today: date, contract_warning_days: int) -> list:
    """Return list of (category, object_id, message) for all currently critical items."""
    items = []
    contract_warning = today + timedelta(days=contract_warning_days)

    # Contracts (DB-side filtering)
    for c in Contract.objects.filter(end_date__lt=today).order_by("end_date"):
        items.append((
            Category.CONTRACT_EXPIRED,
            c.pk,
            f"Vertrag \u201e{c.title}\u201c ({c.vendor}) ist abgelaufen",
        ))
    for c in Contract.objects.filter(
        end_date__gte=today, end_date__lte=contract_warning
    ).order_by("end_date"):
        items.append((
            Category.CONTRACT_EXPIRING,
            c.pk,
            f"Vertrag \u201e{c.title}\u201c ({c.vendor}) l\u00e4uft am {c.end_date} aus",
        ))

    # Maintenance (status is a Python property — must iterate in Python)
    for p in MaintenancePlan.objects.select_related("asset").annotate(
        last_performed_at=Max("records__performed_at")
    ):
        if p.status == MaintenanceStatus.OVERDUE:
            items.append((
                Category.MAINTENANCE_OVERDUE,
                p.pk,
                f"Wartung \u201e{p.title}\u201c ({p.asset}) ist \u00fcberf\u00e4llig",
            ))
        elif p.status == MaintenanceStatus.DUE_SOON:
            items.append((
                Category.MAINTENANCE_DUE_SOON,
                p.pk,
                f"Wartung \u201e{p.title}\u201c ({p.asset}) ist bald f\u00e4llig",
            ))

    # Qualification (status is a Python property)
    for c in QualificationCycle.objects.select_related("asset").annotate(
        last_signed_at=Max("signatures__signed_at")
    ):
        if c.status == QualStatus.OVERDUE:
            items.append((
                Category.QUALIFICATION_OVERDUE,
                c.pk,
                f"Qualifizierung \u201e{c.title}\u201c ({c.asset}) ist \u00fcberf\u00e4llig",
            ))
        elif c.status == QualStatus.DUE_SOON:
            items.append((
                Category.QUALIFICATION_DUE_SOON,
                c.pk,
                f"Qualifizierung \u201e{c.title}\u201c ({c.asset}) ist bald f\u00e4llig",
            ))
        elif c.status == QualStatus.NEVER_SIGNED:
            items.append((
                Category.QUALIFICATION_NEVER_SIGNED,
                c.pk,
                f"Qualifizierung \u201e{c.title}\u201c ({c.asset}) wurde noch nie signiert",
            ))

    # Tasks (DB-side filtering)
    for t in Task.objects.exclude(status="done").filter(due_date__lt=today).order_by("due_date"):
        items.append((
            Category.TASK_OVERDUE,
            t.pk,
            f"Aufgabe \u201e{t.title}\u201c ist \u00fcberf\u00e4llig",
        ))

    return items
