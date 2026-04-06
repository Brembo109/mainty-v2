# User Management UI — Design Spec

**Date:** 2026-04-06  
**Status:** Approved

## Summary

Admin-only CRUD interface for user management within the `accounts` app. Admins can create, edit, deactivate, and delete users, assign roles, and reset passwords. Implemented as standard Django class-based views following the existing module pattern (list → detail → form).

## Approach

Extend `apps/accounts/` with new views, forms, templates, and URLs. No new Django app. All views protected by `RoleRequiredMixin(required_role=Role.ADMIN)`. Password reset sets `password_changed_at = now()` (90-day rotation clock restarts). Delete is blocked when audit entries exist; deactivation (`is_active=False`) is the GMP-safe alternative.

---

## Section 1: Model

No model changes. `User` already provides everything needed:

- `username`, `email`, `first_name`, `last_name`, `is_active` — from `AbstractUser`
- `password_changed_at` — 90-day rotation tracking
- `role` property — reads from Django Groups via `self.groups`
- `set_role(role_name)` — assigns exactly one role group

---

## Section 2: URLs

All under `accounts:` namespace, prefix `/users/`:

| Name | Path | Method | View |
|------|------|--------|------|
| `accounts:user-list` | `/users/` | GET | `UserListView` |
| `accounts:user-create` | `/users/create/` | GET, POST | `UserCreateView` |
| `accounts:user-detail` | `/users/<pk>/` | GET | `UserDetailView` |
| `accounts:user-update` | `/users/<pk>/edit/` | GET, POST | `UserUpdateView` |
| `accounts:user-password` | `/users/<pk>/password/` | GET, POST | `UserPasswordView` |
| `accounts:user-toggle-active` | `/users/<pk>/toggle-active/` | POST | `UserToggleActiveView` |
| `accounts:user-delete` | `/users/<pk>/delete/` | GET, POST | `UserDeleteView` |

---

## Section 3: Forms

All in `apps/accounts/forms.py`. All widgets use `_INPUT_CLASS = "form-input"`.

### `UserCreateForm(forms.ModelForm)`

```python
class Meta:
    model = User
    fields = ["username", "email", "first_name", "last_name"]

role = forms.ChoiceField(choices=Role.CHOICES)
password1 = forms.CharField(widget=forms.PasswordInput)
password2 = forms.CharField(widget=forms.PasswordInput)
```

`save()` override: calls `user.set_password(password1)` and `user.set_role(role)` before returning.

### `UserUpdateForm(forms.ModelForm)`

```python
class Meta:
    model = User
    fields = ["username", "email", "first_name", "last_name", "is_active"]

role = forms.ChoiceField(choices=Role.CHOICES)
```

`__init__` pre-populates `role` from `instance.role`. `save()` calls `user.set_role(role)`.

### `AdminSetPasswordForm(forms.Form)`

```python
new_password1 = forms.CharField(widget=forms.PasswordInput)
new_password2 = forms.CharField(widget=forms.PasswordInput)
```

`clean()` validates both passwords match. View calls `user.set_password()` + `user.password_changed_at = now()` + `user.save()`.

---

## Section 4: Views

All in `apps/accounts/views.py`. All inherit `RoleRequiredMixin` with `required_role = Role.ADMIN`.

### `UserListView(RoleRequiredMixin, ListView)`
- `queryset`: `User.objects.prefetch_related("groups").order_by("username")`
- Template: `accounts/user_list.html`

### `UserCreateView(RoleRequiredMixin, CreateView)`
- `form_class`: `UserCreateForm`
- `success_url`: `reverse_lazy("accounts:user-list")`
- `form_valid`: sets success message

### `UserDetailView(RoleRequiredMixin, DetailView)`
- `queryset`: `User.objects.prefetch_related("groups")`
- Template: `accounts/user_detail.html`

### `UserUpdateView(RoleRequiredMixin, UpdateView)`
- `form_class`: `UserUpdateForm`
- `success_url`: `reverse_lazy("accounts:user-list")`

### `UserPasswordView(RoleRequiredMixin, FormView)`
- `form_class`: `AdminSetPasswordForm`
- `get_object()`: fetches user by `pk` from URL
- `form_valid`: `user.set_password()`, `user.password_changed_at = now()`, `user.save()`
- `success_url`: `reverse_lazy("accounts:user-detail", kwargs={"pk": pk})`

### `UserToggleActiveView(RoleRequiredMixin, View)`
- POST-only (`dispatch` enforces `require_POST`)
- Flips `user.is_active`, saves, redirects to `accounts:user-list`

### `UserDeleteView(RoleRequiredMixin, DeleteView)`
- `get_context_data`: adds `has_audit_entries = AuditLog.objects.filter(actor=self.object).exists()`
- `post`: if `has_audit_entries` → re-render confirm page with error (no delete); else → `super().post()`
- `success_url`: `reverse_lazy("accounts:user-list")`

---

## Section 5: Templates

All `{% extends "base.html" %}`, Admin-only via view access control.

### `accounts/user_list.html`
Table columns: Username, Name, E-Mail, Rolle (badge), Status (Aktiv/Inaktiv badge), Aktionen (Bearbeiten, Deaktivieren/Reaktivieren button as POST form).

### `accounts/user_form.html`
Shared for create + update. Context: `form_title`, `submit_label`. Fields: Benutzerdaten-Gruppe (username, email, first_name, last_name), then Zugang-Gruppe (role, is_active — is_active hidden on create since new users are always active).

### `accounts/user_detail.html`
User info card + quick actions: "Passwort setzen" button, "Deaktivieren/Reaktivieren" POST form button, "Bearbeiten" link, "Löschen" link.

### `accounts/user_password.html`
Simple form: two password fields. Note: "Das 90-Tage-Passwort-Limit wird zurückgesetzt."

### `accounts/user_confirm_delete.html`
Two states rendered by context:
- `has_audit_entries=True`: error message + "Stattdessen deaktivieren" button (POST to toggle-active)
- `has_audit_entries=False`: standard delete confirmation

### `templates/partials/sidebar.html`
Change `href="#"` on the "Benutzer" nav item to `href="{% url 'accounts:user-list' %}"`.

---

## Section 6: Tests

In `apps/accounts/tests.py`. All use `client.force_login()`.

### `UserListViewTest`
- Admin sees list (200)
- User role gets 403
- Viewer role gets 403

### `UserCreateViewTest`
- Admin can create user with role
- Role is correctly assigned via groups
- Passwords must match (validation error otherwise)
- Created user can authenticate with the set password

### `UserUpdateViewTest`
- Admin can update username/email
- Role change is reflected in groups
- `is_active` can be toggled via form

### `AdminSetPasswordTest`
- Admin sets new password for another user
- `password_changed_at` is updated to now
- User can authenticate with new password
- Mismatched passwords return validation error

### `UserToggleActiveTest`
- POST deactivates active user
- POST reactivates inactive user
- GET returns 405

### `UserDeleteViewTest`
- User without audit entries: POST deletes user
- User with audit entries: POST returns 200 with error, user not deleted
- After blocked delete, deactivation button present in response

---

## Out of Scope

- E-Mail-Benachrichtigung bei Passwort-Reset durch Admin
- Selbst-Registrierung (kein Sign-Up Flow)
- Passwort-Policy-Enforcement (Mindestlänge etc.) — Django-Default reicht
- 2FA
