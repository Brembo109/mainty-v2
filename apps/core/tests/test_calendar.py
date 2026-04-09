import pytest
from datetime import date
from apps.core.calendar_utils import build_month_events, ALL_TYPES


@pytest.mark.django_db
def test_build_month_events_returns_dict():
    result = build_month_events(2026, 4, ALL_TYPES)
    assert isinstance(result, dict)
    for key in result:
        assert isinstance(key, date)
    for value in result.values():
        assert isinstance(value, list)
        for event in value:
            assert "type" in event
            assert "label" in event
            assert "url" in event
            assert "dot_color" in event
            assert "text_color" in event


@pytest.mark.django_db
def test_build_month_events_empty_types():
    result = build_month_events(2026, 4, [])
    assert result == {}


@pytest.mark.django_db
def test_build_month_events_only_includes_requested_month(db):
    from apps.tasks.models import Task
    # Task in target month
    task_in = Task.objects.create(
        title="In month",
        due_date=date(2026, 4, 15),
        status="open",
        priority="medium",
        change_reason="test",
    )
    # Task outside target month
    task_out = Task.objects.create(
        title="Out of month",
        due_date=date(2026, 5, 1),
        status="open",
        priority="medium",
        change_reason="test",
    )
    result = build_month_events(2026, 4, ["task"])
    all_labels = [e["label"] for events in result.values() for e in events]
    assert "In month" in all_labels
    assert "Out of month" not in all_labels


@pytest.mark.django_db
def test_build_month_events_done_tasks_excluded():
    from apps.tasks.models import Task
    Task.objects.create(
        title="Done task",
        due_date=date(2026, 4, 10),
        status="done",
        priority="medium",
        change_reason="test",
    )
    result = build_month_events(2026, 4, ["task"])
    all_labels = [e["label"] for events in result.values() for e in events]
    assert "Done task" not in all_labels


@pytest.mark.django_db
def test_build_month_events_calibration_skips_at_lab_and_never(db):
    from apps.calibration.models import TestEquipment, CalibrationRecord
    # Equipment with no records → status NEVER → excluded
    eq = TestEquipment.objects.create(
        name="Waage",
        serial_number="SN-001",
        calibration_interval_days=365,
    )
    result = build_month_events(2026, 4, ["calibration"])
    all_labels = [e["label"] for events in result.values() for e in events]
    assert "Waage" not in all_labels
