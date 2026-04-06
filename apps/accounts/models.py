from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    THEME_CHOICES = [("dark", "Dark"), ("light", "Light")]

    password_changed_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=_("Passwort geändert am"),
    )
    theme = models.CharField(
        max_length=5,
        choices=THEME_CHOICES,
        default="dark",
        verbose_name=_("Theme"),
    )

    class Meta:
        verbose_name = _("Benutzer")
        verbose_name_plural = _("Benutzer")

    @property
    def role(self):
        """Return the user's role name, or None if no role group is assigned.

        Uses `.all()` so Django's prefetch_related cache is respected — no
        extra queries when groups have been prefetched by the caller.
        """
        from .constants import Role
        group_names = {g.name for g in self.groups.all()}
        for role_name in Role.ALL:
            if role_name in group_names:
                return role_name
        return None

    def set_role(self, role_name):
        """Assign a role, removing all other role groups first.

        Ensures each user belongs to exactly one role group.
        """
        from django.contrib.auth.models import Group
        from .constants import Role

        self.groups.remove(*self.groups.filter(name__in=Role.ALL))
        if role_name:
            group = Group.objects.get(name=role_name)
            self.groups.add(group)

    def has_role(self, *role_names):
        """Return True if the user belongs to any of the given role groups."""
        return self.groups.filter(name__in=role_names).exists()
