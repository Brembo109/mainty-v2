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
        OPEN: "status-dot status-dot-info",
        IN_PROGRESS: "status-dot status-dot-warn",
        DONE: "status-dot status-dot-ok",
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
        LOW: "status-dot status-dot-idle",
        MEDIUM: "status-dot status-dot-warn",
        HIGH: "status-dot status-dot-danger",
    }

    LABEL = {
        LOW: _("Niedrig"),
        MEDIUM: _("Mittel"),
        HIGH: _("Hoch"),
    }
