from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.audit.mixins import AuditedModel

from .constants import TaskPriority, TaskStatus


class Task(AuditedModel):
    title = models.CharField(max_length=255, verbose_name=_("Titel"))
    description = models.TextField(blank=True, verbose_name=_("Beschreibung"))
    asset = models.ForeignKey(
        "assets.Asset",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="tasks",
        verbose_name=_("Anlage"),
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_tasks",
        verbose_name=_("Zugewiesen an"),
    )
    due_date = models.DateField(null=True, blank=True, verbose_name=_("Fällig am"))
    priority = models.CharField(
        max_length=10,
        choices=TaskPriority.CHOICES,
        default=TaskPriority.MEDIUM,
        db_index=True,
        verbose_name=_("Priorität"),
    )
    status = models.CharField(
        max_length=15,
        choices=TaskStatus.CHOICES,
        default=TaskStatus.OPEN,
        db_index=True,
        verbose_name=_("Status"),
    )
    change_reason = models.TextField(blank=True, verbose_name=_("Änderungsgrund"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["status", "-priority", "due_date"]
        verbose_name = _("Aufgabe")
        verbose_name_plural = _("Aufgaben")

    def __str__(self):
        return self.title

    @property
    def status_label(self):
        return TaskStatus.LABEL.get(self.status, self.status)

    @property
    def status_badge_class(self):
        return TaskStatus.BADGE_CLASS.get(self.status, "badge-neutral")

    @property
    def priority_label(self):
        return TaskPriority.LABEL.get(self.priority, self.priority)

    @property
    def priority_badge_class(self):
        return TaskPriority.BADGE_CLASS.get(self.priority, "badge-neutral")

    @property
    def is_overdue(self):
        from datetime import date
        return (
            self.due_date is not None
            and self.due_date < date.today()
            and self.status != TaskStatus.DONE
        )
