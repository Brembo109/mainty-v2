import calendar
from collections import defaultdict
from datetime import date, timedelta

from django.urls import reverse
from django.db.models import Max

ALL_TYPES = ["maintenance", "qualification", "task", "calibration", "contract"]

# Per-type visual config
_TYPE_CONFIG = {
    "maintenance": {"dot_color": "bg-status-danger", "text_color": "text-status-danger"},
    "qualification": {"dot_color": "bg-status-warning", "text_color": "text-status-warning"},
    "task": {"dot_color": "bg-status-success", "text_color": "text-status-success"},
    "calibration": {"dot_color": "bg-blue-400", "text_color": "text-blue-400"},
    "contract": {"dot_color": "bg-purple-400", "text_color": "text-purple-400"},
}


def build_month_events(year: int, month: int, types: list) -> dict:
    """
    Returns {date: [event_dict]} for all matching events in the given month.

    event_dict keys: type, label, url, dot_color, text_color
    """
    if not types:
        return {}

    from apps.maintenance.models import MaintenancePlan
    from apps.qualification.models import QualificationCycle
    from apps.tasks.models import Task
    from apps.calibration.models import TestEquipment
    from apps.calibration.constants import CalibrationStatus
    from apps.contracts.models import Contract

    first_day = date(year, month, 1)
    last_day = date(year, month, calendar.monthrange(year, month)[1])
    events = defaultdict(list)

    if "maintenance" in types:
        plans = MaintenancePlan.objects.select_related("asset").annotate(
            last_performed_at=Max("records__performed_at")
        )
        for plan in plans:
            nd = plan.next_due
            if nd is not None and first_day <= nd <= last_day:
                events[nd].append({
                    "type": "maintenance",
                    "label": str(plan),
                    "url": reverse("maintenance:detail", args=[plan.pk]),
                    **_TYPE_CONFIG["maintenance"],
                })

    if "qualification" in types:
        cycles = QualificationCycle.objects.select_related("asset").annotate(
            last_signed_at=Max("signatures__signed_at")
        )
        for cycle in cycles:
            nd = cycle.next_due
            if nd is not None and first_day <= nd <= last_day:
                events[nd].append({
                    "type": "qualification",
                    "label": str(cycle),
                    "url": reverse("qualification:detail", args=[cycle.pk]),
                    **_TYPE_CONFIG["qualification"],
                })

    if "task" in types:
        tasks = Task.objects.filter(
            due_date__year=year,
            due_date__month=month,
        ).exclude(status="done")
        for task in tasks:
            events[task.due_date].append({
                "type": "task",
                "label": task.title,
                "url": reverse("tasks:detail", args=[task.pk]),
                **_TYPE_CONFIG["task"],
            })

    if "calibration" in types:
        equipment_list = TestEquipment.objects.prefetch_related("records")
        for eq in equipment_list:
            if eq.status in (CalibrationStatus.AT_LAB, CalibrationStatus.NEVER):
                continue
            nd = eq.next_due
            if nd is not None and first_day <= nd <= last_day:
                events[nd].append({
                    "type": "calibration",
                    "label": eq.name,
                    "url": reverse("calibration:detail", args=[eq.pk]),
                    **_TYPE_CONFIG["calibration"],
                })

    if "contract" in types:
        contracts = Contract.objects.filter(
            end_date__year=year,
            end_date__month=month,
        )
        for contract in contracts:
            events[contract.end_date].append({
                "type": "contract",
                "label": contract.title,
                "url": reverse("contracts:detail", args=[contract.pk]),
                **_TYPE_CONFIG["contract"],
            })

    return dict(events)


def build_day_events(target_date: date, types: list) -> list:
    """Returns list of event_dicts for a single date."""
    return build_month_events(target_date.year, target_date.month, types).get(
        target_date, []
    )
