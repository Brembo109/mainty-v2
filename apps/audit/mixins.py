from django.db import models


class AuditedModel(models.Model):
    """Abstract base class that opts a model into automatic audit logging.

    Inherit this mixin on any GMP-relevant model to have CREATE, UPDATE, and
    DELETE events automatically recorded in AuditLog via Django signals.
    Signals are wired in AuditConfig.ready() for every registered subclass.

    Usage::

        class Equipment(AuditedModel):
            name = models.CharField(max_length=255)
    """

    class Meta:
        abstract = True
