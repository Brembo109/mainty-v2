from django.utils.translation import gettext_lazy as _


class TaskStatus:
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    DONE = "done"

    CHOICES = [
        (OPEN, _("Offen")),
        (IN_PROGRESS, _("In Bearbeitung")),
        (DONE, _("Erledigt")),
    ]

    BADGE_CLASS = {
        OPEN: "badge-neutral border border-border",
        IN_PROGRESS: "badge-warning border border-status-warning",
        DONE: "badge-success border border-status-success",
    }

    LABEL = {
        OPEN: _("Offen"),
        IN_PROGRESS: _("In Bearbeitung"),
        DONE: _("Erledigt"),
    }


class TaskPriority:
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    CHOICES = [
        (LOW, _("Niedrig")),
        (MEDIUM, _("Mittel")),
        (HIGH, _("Hoch")),
    ]

    BADGE_CLASS = {
        LOW: "badge-neutral border border-border",
        MEDIUM: "badge-warning border border-status-warning",
        HIGH: "badge-danger border border-status-danger",
    }

    LABEL = {
        LOW: _("Niedrig"),
        MEDIUM: _("Mittel"),
        HIGH: _("Hoch"),
    }
