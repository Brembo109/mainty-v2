"""Signal handlers for the audit trail.

Model signals (pre_save / post_save / post_delete) are connected explicitly
via connect_audit_signals() which is called from AuditConfig.ready() for every
AuditedModel subclass.

Auth signals use the @receiver decorator and are auto-registered when this
module is imported (also in AuditConfig.ready()).

Every connection uses a stable dispatch_uid to prevent duplicate handlers when
Django's dev-server reloader calls ready() more than once in a process.
"""

from decimal import Decimal

from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from .constants import Action
from .middleware import get_current_ip, get_current_user


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _field_values(instance):
    """Return {field_name: json_safe_value} for all concrete fields."""
    data = {}
    for field in instance._meta.concrete_fields:
        try:
            value = field.value_from_object(instance)
            if hasattr(value, "isoformat"):
                value = value.isoformat()
            elif isinstance(value, Decimal):
                # Normalise to a canonical string so change-detection stays stable
                # across DB round-trips (e.g. "10.5" vs "10.500").
                value = str(value.normalize())
            elif not isinstance(value, (int, float, bool, str, type(None))):
                value = str(value)
            data[field.name] = value
        except Exception:
            pass
    return data


def _compute_changes(old_data, new_data):
    """Return {field: [old, new]} for fields whose value changed."""
    return {
        key: [old_data.get(key), new_val]
        for key, new_val in new_data.items()
        if old_data.get(key) != new_val
    }


def _ip_from_request(request):
    if request is None:
        return None
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def _write(*, actor, actor_username, action, content_type=None,
           object_id="", object_repr="", changes=None, ip_address=None):
    from .models import AuditLog
    AuditLog.objects.create(
        actor=actor,
        actor_username=actor_username,
        action=action,
        content_type=content_type,
        object_id=object_id,
        object_repr=object_repr[:255],
        changes=changes or {},
        ip_address=ip_address,
    )


# ---------------------------------------------------------------------------
# Model signal handlers
# ---------------------------------------------------------------------------

def _pre_save_handler(sender, instance, **kwargs):
    """Snapshot the current DB state before save so UPDATE diffs are accurate.

    Skipped outside of a request context (management commands, fixtures) to
    avoid unexpected DB queries during bulk data operations.
    """
    if instance.pk and get_current_user() is not None:
        try:
            current = sender.objects.get(pk=instance.pk)
            instance._audit_snapshot = _field_values(current)
        except sender.DoesNotExist:
            instance._audit_snapshot = {}
    else:
        instance._audit_snapshot = {}


def _post_save_handler(sender, instance, created, **kwargs):
    from django.contrib.contenttypes.models import ContentType

    user = get_current_user()
    actor_username = user.get_username() if user else ""

    if created:
        changes = _field_values(instance)
        action = Action.CREATE
    else:
        old_data = getattr(instance, "_audit_snapshot", {})
        changes = _compute_changes(old_data, _field_values(instance))
        if not changes:
            return  # nothing meaningful changed — skip
        action = Action.UPDATE

    _write(
        actor=user,
        actor_username=actor_username,
        action=action,
        content_type=ContentType.objects.get_for_model(sender),
        object_id=str(instance.pk),
        object_repr=str(instance),
        changes=changes,
        ip_address=get_current_ip(),
    )


def _post_delete_handler(sender, instance, **kwargs):
    from django.contrib.contenttypes.models import ContentType

    user = get_current_user()
    _write(
        actor=user,
        actor_username=user.get_username() if user else "",
        action=Action.DELETE,
        content_type=ContentType.objects.get_for_model(sender),
        object_id=str(instance.pk),
        object_repr=str(instance),
        ip_address=get_current_ip(),
    )


def connect_audit_signals(model_class):
    """Wire pre_save / post_save / post_delete to the given model class.

    Uses stable dispatch_uid values so Django's deduplication prevents
    double-registration when ready() is called more than once.
    """
    label = model_class._meta.label
    pre_save.connect(
        _pre_save_handler, sender=model_class, weak=False,
        dispatch_uid=f"audit.pre_save.{label}",
    )
    post_save.connect(
        _post_save_handler, sender=model_class, weak=False,
        dispatch_uid=f"audit.post_save.{label}",
    )
    post_delete.connect(
        _post_delete_handler, sender=model_class, weak=False,
        dispatch_uid=f"audit.post_delete.{label}",
    )


# ---------------------------------------------------------------------------
# Auth signal handlers
# ---------------------------------------------------------------------------

@receiver(user_logged_in, dispatch_uid="audit.on_login")
def on_login(sender, request, user, **kwargs):
    _write(
        actor=user,
        actor_username=user.get_username(),
        action=Action.LOGIN,
        ip_address=_ip_from_request(request),
    )


@receiver(user_logged_out, dispatch_uid="audit.on_logout")
def on_logout(sender, request, user, **kwargs):
    if user is None:
        return
    _write(
        actor=user,
        actor_username=user.get_username(),
        action=Action.LOGOUT,
        ip_address=_ip_from_request(request),
    )


@receiver(user_login_failed, dispatch_uid="audit.on_login_failed")
def on_login_failed(sender, credentials, request, **kwargs):
    _write(
        actor=None,
        actor_username=str(credentials.get("username", ""))[:150],
        action=Action.LOGIN_FAILED,
        ip_address=_ip_from_request(request),
    )
