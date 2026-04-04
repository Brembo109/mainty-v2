from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import PermissionDenied


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
