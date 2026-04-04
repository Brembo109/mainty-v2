from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import PermissionDenied

from .constants import Role


class WriteAccessMixin(AccessMixin):
    """Allow Admin and User roles to write; Viewer (and anonymous) get 403.

    Use on CreateView, UpdateView, DeleteView across all apps.
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.has_role(Role.ADMIN, Role.USER):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class RoleRequiredMixin(AccessMixin):
    """Restrict a class-based view to users with a specific role.

    Usage::

        class MyView(RoleRequiredMixin, View):
            required_role = Role.ADMIN
    """

    required_role = None

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if self.required_role and not request.user.has_role(self.required_role):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
