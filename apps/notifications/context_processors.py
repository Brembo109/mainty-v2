from datetime import date

from django.db.models import Q

from apps.core.models import SiteConfig

from .collector import collect_critical_items
from .models import Notification


def notifications(request):
    """Sync critical-item notifications for the current user and return badge count."""
    if not request.user.is_authenticated:
        return {}

    config = SiteConfig.get()
    today = date.today()
    items = collect_critical_items(today, config.contract_expiry_warning_days)

    current_keys = set()
    for category, object_id, message in items:
        Notification.objects.get_or_create(
            user=request.user,
            category=category,
            object_id=object_id,
            defaults={"message": message},
        )
        current_keys.add((category, object_id))

    # Auto-resolve: delete notifications whose item is no longer critical
    if current_keys:
        valid_q = Q()
        for category, object_id in current_keys:
            valid_q |= Q(category=category, object_id=object_id)
        Notification.objects.filter(user=request.user).exclude(valid_q).delete()
    else:
        Notification.objects.filter(user=request.user).delete()

    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    return {"notification_unread_count": unread_count}
