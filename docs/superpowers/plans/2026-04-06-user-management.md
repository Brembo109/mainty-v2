# User Management UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an Admin-only CRUD interface for managing users (create, edit, deactivate, delete, password reset) within the existing `accounts` app.

**Architecture:** New views, forms, and templates added directly to `apps/accounts/`. All views protected by `RoleRequiredMixin(required_role=Role.ADMIN)`. No model changes — `User` already has `set_role()`, `role`, and `is_active`. Delete is guarded by an audit-entry check; deactivation is the GMP-safe fallback.

**Tech Stack:** Django 5, `RoleRequiredMixin`, `AuditLog`, Django Groups for roles, Tailwind CSS, Django TestCase with `force_login`.

---

## File Map

| File | Action | Purpose |
|------|--------|---------|
| `apps/accounts/forms.py` | Modify | Add `UserCreateForm`, `UserUpdateForm`, `AdminSetPasswordForm` |
| `apps/accounts/views.py` | Modify | Add 7 new CBVs for user CRUD |
| `apps/accounts/urls.py` | Modify | Register 7 new URL patterns |
| `apps/accounts/tests.py` | Modify | Add form + view tests |
| `templates/accounts/user_list.html` | Create | User table with role badge and actions |
| `templates/accounts/user_form.html` | Create | Shared create/update form |
| `templates/accounts/user_detail.html` | Create | User detail with quick-action buttons |
| `templates/accounts/user_password.html` | Create | Admin password-reset form |
| `templates/accounts/user_confirm_delete.html` | Create | Delete confirmation or audit-guard error |
| `templates/partials/sidebar.html` | Modify | Wire "Benutzer" link to `accounts:user-list` |

---

## Task 1: Forms

**Files:**
- Modify: `apps/accounts/forms.py`
- Modify: `apps/accounts/tests.py`

- [ ] **Step 1: Write failing tests**

Append to `apps/accounts/tests.py`:

```python
from django.contrib.auth.models import Group

from apps.accounts.constants import Role
from apps.accounts.forms import AdminSetPasswordForm, UserCreateForm, UserUpdateForm


def _setup_roles():
    """Create role groups — required before any set_role() call."""
    for name in Role.ALL:
        Group.objects.get_or_create(name=name)


def _make_admin(username="admin"):
    _setup_roles()
    user = User.objects.create_user(username=username, password="adminpass123")
    user.set_role(Role.ADMIN)
    return user


class UserCreateFormTest(TestCase):
    def setUp(self):
        _setup_roles()

    def _valid_data(self, **overrides):
        data = {
            "username": "newuser",
            "email": "new@example.com",
            "first_name": "Max",
            "last_name": "Muster",
            "role": Role.USER,
            "password1": "sicher1234!",
            "password2": "sicher1234!",
        }
        data.update(overrides)
        return data

    def test_valid_form_creates_user_with_role(self):
        form = UserCreateForm(data=self._valid_data())
        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()
        self.assertEqual(user.role, Role.USER)

    def test_password_mismatch_invalid(self):
        form = UserCreateForm(data=self._valid_data(password2="wrong"))
        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)

    def test_password_stored_hashed(self):
        form = UserCreateForm(data=self._valid_data())
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertTrue(user.check_password("sicher1234!"))
        self.assertNotEqual(user.password, "sicher1234!")


class UserUpdateFormTest(TestCase):
    def setUp(self):
        _setup_roles()
        self.user = User.objects.create_user(username="testuser", password="pass")
        self.user.set_role(Role.USER)

    def test_role_pre_populated(self):
        form = UserUpdateForm(instance=self.user)
        self.assertEqual(form.fields["role"].initial, Role.USER)

    def test_role_change_saved(self):
        form = UserUpdateForm(
            data={
                "username": "testuser",
                "email": "",
                "first_name": "",
                "last_name": "",
                "is_active": True,
                "role": Role.VIEWER,
            },
            instance=self.user,
        )
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        self.user.refresh_from_db()
        self.assertEqual(self.user.role, Role.VIEWER)


class AdminSetPasswordFormTest(TestCase):
    def test_valid_passwords_match(self):
        form = AdminSetPasswordForm(
            data={"new_password1": "neuesPasswort1!", "new_password2": "neuesPasswort1!"}
        )
        self.assertTrue(form.is_valid())

    def test_mismatch_invalid(self):
        form = AdminSetPasswordForm(
            data={"new_password1": "neuesPasswort1!", "new_password2": "falsch"}
        )
        self.assertFalse(form.is_valid())
        self.assertIn("new_password2", form.errors)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
docker compose exec web python manage.py test apps.accounts.tests.UserCreateFormTest apps.accounts.tests.UserUpdateFormTest apps.accounts.tests.AdminSetPasswordFormTest -v 2
```

Expected: ImportError or AttributeError — forms don't exist yet.

- [ ] **Step 3: Implement the three forms**

Replace the full content of `apps/accounts/forms.py` with:

```python
from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    SetPasswordForm,
)
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .constants import Role
from .models import User

_FORM_INPUT_CLASS = "form-input"


class LoginForm(AuthenticationForm):
    """Login form with localised error messages and Vercel-dark CSS classes."""

    error_messages = {
        "invalid_login": _("Benutzername oder Passwort falsch."),
        "inactive": _("Dieses Konto ist deaktiviert."),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({
            "class": _FORM_INPUT_CLASS,
            "placeholder": "",
            "autofocus": True,
        })
        self.fields["password"].widget.attrs.update({
            "class": _FORM_INPUT_CLASS,
            "placeholder": "",
        })


def _apply_form_input_class(form):
    """Add the form-input CSS class to all fields of a form instance."""
    for field in form.fields.values():
        field.widget.attrs.setdefault("class", _FORM_INPUT_CLASS)


class StyledPasswordChangeForm(PasswordChangeForm):
    """PasswordChangeForm with Vercel-dark CSS classes on all fields."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_form_input_class(self)


class StyledSetPasswordForm(SetPasswordForm):
    """SetPasswordForm (used for reset + expired) with Vercel-dark CSS classes."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_form_input_class(self)


class UserCreateForm(forms.ModelForm):
    role = forms.ChoiceField(
        choices=Role.CHOICES,
        label=_("Rolle"),
        widget=forms.Select(attrs={"class": _FORM_INPUT_CLASS}),
    )
    password1 = forms.CharField(
        label=_("Passwort"),
        widget=forms.PasswordInput(attrs={"class": _FORM_INPUT_CLASS}),
    )
    password2 = forms.CharField(
        label=_("Passwort bestätigen"),
        widget=forms.PasswordInput(attrs={"class": _FORM_INPUT_CLASS}),
    )

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name"]
        widgets = {
            "username": forms.TextInput(attrs={"class": _FORM_INPUT_CLASS}),
            "email": forms.EmailInput(attrs={"class": _FORM_INPUT_CLASS}),
            "first_name": forms.TextInput(attrs={"class": _FORM_INPUT_CLASS}),
            "last_name": forms.TextInput(attrs={"class": _FORM_INPUT_CLASS}),
        }

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password1")
        p2 = cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", _("Die Passwörter stimmen nicht überein."))
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
            user.set_role(self.cleaned_data["role"])
        return user


class UserUpdateForm(forms.ModelForm):
    role = forms.ChoiceField(
        choices=Role.CHOICES,
        label=_("Rolle"),
        widget=forms.Select(attrs={"class": _FORM_INPUT_CLASS}),
    )

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name", "is_active"]
        widgets = {
            "username": forms.TextInput(attrs={"class": _FORM_INPUT_CLASS}),
            "email": forms.EmailInput(attrs={"class": _FORM_INPUT_CLASS}),
            "first_name": forms.TextInput(attrs={"class": _FORM_INPUT_CLASS}),
            "last_name": forms.TextInput(attrs={"class": _FORM_INPUT_CLASS}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["role"].initial = self.instance.role

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            user.set_role(self.cleaned_data["role"])
        return user


class AdminSetPasswordForm(forms.Form):
    new_password1 = forms.CharField(
        label=_("Neues Passwort"),
        widget=forms.PasswordInput(attrs={"class": _FORM_INPUT_CLASS}),
    )
    new_password2 = forms.CharField(
        label=_("Passwort bestätigen"),
        widget=forms.PasswordInput(attrs={"class": _FORM_INPUT_CLASS}),
    )

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("new_password1")
        p2 = cleaned_data.get("new_password2")
        if p1 and p2 and p1 != p2:
            self.add_error("new_password2", _("Die Passwörter stimmen nicht überein."))
        return cleaned_data
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
docker compose exec web python manage.py test apps.accounts.tests.UserCreateFormTest apps.accounts.tests.UserUpdateFormTest apps.accounts.tests.AdminSetPasswordFormTest -v 2
```

Expected: OK (7 tests pass)

- [ ] **Step 5: Commit**

```bash
git add apps/accounts/forms.py apps/accounts/tests.py
git commit -m "feat: add UserCreateForm, UserUpdateForm, AdminSetPasswordForm"
```

---

## Task 2: Views + URLs

**Files:**
- Modify: `apps/accounts/views.py`
- Modify: `apps/accounts/urls.py`
- Modify: `apps/accounts/tests.py`

- [ ] **Step 1: Write failing tests**

Append to `apps/accounts/tests.py`:

```python
from apps.audit.models import AuditLog


class UserListViewTest(TestCase):
    def setUp(self):
        self.admin = _make_admin("admin_list")
        self.client.force_login(self.admin)

    def test_admin_sees_list(self):
        response = self.client.get(reverse("accounts:user-list"))
        self.assertEqual(response.status_code, 200)

    def test_user_role_gets_403(self):
        _setup_roles()
        u = User.objects.create_user(username="userrole", password="pass")
        u.set_role(Role.USER)
        self.client.force_login(u)
        response = self.client.get(reverse("accounts:user-list"))
        self.assertEqual(response.status_code, 403)

    def test_viewer_role_gets_403(self):
        _setup_roles()
        v = User.objects.create_user(username="viewerrole", password="pass")
        v.set_role(Role.VIEWER)
        self.client.force_login(v)
        response = self.client.get(reverse("accounts:user-list"))
        self.assertEqual(response.status_code, 403)


class UserCreateViewTest(TestCase):
    def setUp(self):
        self.admin = _make_admin("admin_create")
        self.client.force_login(self.admin)

    def test_get_returns_form(self):
        response = self.client.get(reverse("accounts:user-create"))
        self.assertEqual(response.status_code, 200)

    def test_post_creates_user_with_role(self):
        response = self.client.post(
            reverse("accounts:user-create"),
            {
                "username": "brandnew",
                "email": "",
                "first_name": "",
                "last_name": "",
                "role": Role.USER,
                "password1": "sicher1234!",
                "password2": "sicher1234!",
            },
        )
        self.assertRedirects(response, reverse("accounts:user-list"), fetch_redirect_response=False)
        user = User.objects.get(username="brandnew")
        self.assertEqual(user.role, Role.USER)

    def test_password_mismatch_shows_error(self):
        response = self.client.post(
            reverse("accounts:user-create"),
            {
                "username": "brandnew2",
                "email": "",
                "first_name": "",
                "last_name": "",
                "role": Role.USER,
                "password1": "sicher1234!",
                "password2": "falsch",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="brandnew2").exists())


class UserUpdateViewTest(TestCase):
    def setUp(self):
        self.admin = _make_admin("admin_update")
        self.client.force_login(self.admin)
        _setup_roles()
        self.target = User.objects.create_user(username="target", password="pass")
        self.target.set_role(Role.USER)

    def test_get_returns_form(self):
        response = self.client.get(reverse("accounts:user-update", kwargs={"pk": self.target.pk}))
        self.assertEqual(response.status_code, 200)

    def test_post_updates_role(self):
        self.client.post(
            reverse("accounts:user-update", kwargs={"pk": self.target.pk}),
            {
                "username": "target",
                "email": "",
                "first_name": "",
                "last_name": "",
                "is_active": True,
                "role": Role.VIEWER,
            },
        )
        self.target.refresh_from_db()
        self.assertEqual(self.target.role, Role.VIEWER)


class AdminSetPasswordViewTest(TestCase):
    def setUp(self):
        self.admin = _make_admin("admin_pw")
        self.client.force_login(self.admin)
        self.target = User.objects.create_user(username="pwuser", password="oldpass")

    def test_get_returns_form(self):
        response = self.client.get(reverse("accounts:user-password", kwargs={"pk": self.target.pk}))
        self.assertEqual(response.status_code, 200)

    def test_post_sets_password_and_resets_clock(self):
        from django.utils import timezone as tz
        before = tz.now()
        self.client.post(
            reverse("accounts:user-password", kwargs={"pk": self.target.pk}),
            {"new_password1": "neuesPass1!", "new_password2": "neuesPass1!"},
        )
        self.target.refresh_from_db()
        self.assertTrue(self.target.check_password("neuesPass1!"))
        self.assertGreaterEqual(self.target.password_changed_at, before)

    def test_mismatch_shows_error(self):
        response = self.client.post(
            reverse("accounts:user-password", kwargs={"pk": self.target.pk}),
            {"new_password1": "neuesPass1!", "new_password2": "falsch"},
        )
        self.assertEqual(response.status_code, 200)
        self.target.refresh_from_db()
        self.assertTrue(self.target.check_password("oldpass"))  # unchanged


class UserToggleActiveViewTest(TestCase):
    def setUp(self):
        self.admin = _make_admin("admin_toggle")
        self.client.force_login(self.admin)
        self.target = User.objects.create_user(username="toggleuser", password="pass", is_active=True)

    def test_post_deactivates_user(self):
        self.client.post(reverse("accounts:user-toggle-active", kwargs={"pk": self.target.pk}))
        self.target.refresh_from_db()
        self.assertFalse(self.target.is_active)

    def test_post_reactivates_user(self):
        self.target.is_active = False
        self.target.save()
        self.client.post(reverse("accounts:user-toggle-active", kwargs={"pk": self.target.pk}))
        self.target.refresh_from_db()
        self.assertTrue(self.target.is_active)

    def test_get_returns_405(self):
        response = self.client.get(reverse("accounts:user-toggle-active", kwargs={"pk": self.target.pk}))
        self.assertEqual(response.status_code, 405)


class UserDeleteViewTest(TestCase):
    def setUp(self):
        self.admin = _make_admin("admin_del")
        self.client.force_login(self.admin)

    def test_user_without_audit_entries_is_deleted(self):
        target = User.objects.create_user(username="nodelete", password="pass")
        self.client.post(reverse("accounts:user-delete", kwargs={"pk": target.pk}))
        self.assertFalse(User.objects.filter(username="nodelete").exists())

    def test_user_with_audit_entries_is_not_deleted(self):
        target = User.objects.create_user(username="audited", password="pass")
        AuditLog.objects.create(actor=target, actor_username="audited", action="CREATE")
        response = self.client.post(reverse("accounts:user-delete", kwargs={"pk": target.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(username="audited").exists())

    def test_blocked_delete_shows_deactivate_button(self):
        target = User.objects.create_user(username="audited2", password="pass")
        AuditLog.objects.create(actor=target, actor_username="audited2", action="CREATE")
        response = self.client.post(reverse("accounts:user-delete", kwargs={"pk": target.pk}))
        self.assertContains(response, "toggle-active")
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
docker compose exec web python manage.py test apps.accounts.tests.UserListViewTest apps.accounts.tests.UserCreateViewTest apps.accounts.tests.UserUpdateViewTest apps.accounts.tests.AdminSetPasswordViewTest apps.accounts.tests.UserToggleActiveViewTest apps.accounts.tests.UserDeleteViewTest -v 2
```

Expected: FAIL — URLs don't exist yet (NoReverseMatch).

- [ ] **Step 3: Add the 7 views to `apps/accounts/views.py`**

Add these imports at the top (after existing imports):

```python
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView, FormView, View

from apps.audit.models import AuditLog
from .constants import Role
from .forms import AdminSetPasswordForm, LoginForm, StyledPasswordChangeForm, StyledSetPasswordForm, UserCreateForm, UserUpdateForm
from .mixins import RoleRequiredMixin
from .models import User
```

Then append the 7 views at the bottom of `apps/accounts/views.py`:

```python
class UserListView(RoleRequiredMixin, ListView):
    required_role = Role.ADMIN
    model = User
    template_name = "accounts/user_list.html"
    context_object_name = "users"

    def get_queryset(self):
        return User.objects.prefetch_related("groups").order_by("username")


class UserCreateView(RoleRequiredMixin, CreateView):
    required_role = Role.ADMIN
    model = User
    form_class = UserCreateForm
    template_name = "accounts/user_form.html"
    success_url = reverse_lazy("accounts:user-list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form_title"] = _("Neuen Benutzer anlegen")
        ctx["submit_label"] = _("Benutzer erstellen")
        return ctx

    def form_valid(self, form):
        messages.success(self.request, _("Benutzer wurde erfolgreich erstellt."))
        return super().form_valid(form)


class UserDetailView(RoleRequiredMixin, DetailView):
    required_role = Role.ADMIN
    model = User
    template_name = "accounts/user_detail.html"
    context_object_name = "target_user"

    def get_queryset(self):
        return User.objects.prefetch_related("groups")


class UserUpdateView(RoleRequiredMixin, UpdateView):
    required_role = Role.ADMIN
    model = User
    form_class = UserUpdateForm
    template_name = "accounts/user_form.html"
    context_object_name = "target_user"
    success_url = reverse_lazy("accounts:user-list")

    def get_queryset(self):
        return User.objects.prefetch_related("groups")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form_title"] = _("Benutzer bearbeiten")
        ctx["submit_label"] = _("Änderungen speichern")
        return ctx

    def form_valid(self, form):
        messages.success(self.request, _("Benutzer wurde erfolgreich aktualisiert."))
        return super().form_valid(form)


class UserPasswordView(RoleRequiredMixin, FormView):
    required_role = Role.ADMIN
    template_name = "accounts/user_password.html"
    form_class = AdminSetPasswordForm

    def get_target_user(self):
        return get_object_or_404(User, pk=self.kwargs["pk"])

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["target_user"] = self.get_target_user()
        return ctx

    def form_valid(self, form):
        user = self.get_target_user()
        user.set_password(form.cleaned_data["new_password1"])
        user.password_changed_at = timezone.now()
        user.save(update_fields=["password", "password_changed_at"])
        messages.success(self.request, _("Passwort wurde erfolgreich gesetzt."))
        return redirect("accounts:user-detail", pk=user.pk)


class UserToggleActiveView(RoleRequiredMixin, View):
    required_role = Role.ADMIN

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        user.is_active = not user.is_active
        user.save(update_fields=["is_active"])
        if user.is_active:
            messages.success(request, _(f"Benutzer {user.username} wurde aktiviert."))
        else:
            messages.success(request, _(f"Benutzer {user.username} wurde deaktiviert."))
        return redirect("accounts:user-list")


class UserDeleteView(RoleRequiredMixin, DeleteView):
    required_role = Role.ADMIN
    model = User
    template_name = "accounts/user_confirm_delete.html"
    context_object_name = "target_user"
    success_url = reverse_lazy("accounts:user-list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["has_audit_entries"] = AuditLog.objects.filter(actor=self.object).exists()
        return ctx

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if AuditLog.objects.filter(actor=self.object).exists():
            ctx = self.get_context_data()
            return self.render_to_response(ctx)
        messages.success(request, _(f"Benutzer {self.object.username} wurde gelöscht."))
        return super().post(request, *args, **kwargs)
```

- [ ] **Step 4: Register URLs in `apps/accounts/urls.py`**

Add the following 7 paths to `urlpatterns` (after the `set-theme` path):

```python
    path("users/", views.UserListView.as_view(), name="user-list"),
    path("users/create/", views.UserCreateView.as_view(), name="user-create"),
    path("users/<int:pk>/", views.UserDetailView.as_view(), name="user-detail"),
    path("users/<int:pk>/edit/", views.UserUpdateView.as_view(), name="user-update"),
    path("users/<int:pk>/password/", views.UserPasswordView.as_view(), name="user-password"),
    path("users/<int:pk>/toggle-active/", views.UserToggleActiveView.as_view(), name="user-toggle-active"),
    path("users/<int:pk>/delete/", views.UserDeleteView.as_view(), name="user-delete"),
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
docker compose exec web python manage.py test apps.accounts.tests.UserListViewTest apps.accounts.tests.UserCreateViewTest apps.accounts.tests.UserUpdateViewTest apps.accounts.tests.AdminSetPasswordViewTest apps.accounts.tests.UserToggleActiveViewTest apps.accounts.tests.UserDeleteViewTest -v 2
```

Expected: OK (16 tests pass)

- [ ] **Step 6: Run full test suite**

```bash
docker compose exec web python manage.py test -v 2 2>&1 | tail -8
```

Expected: OK (all tests pass)

- [ ] **Step 7: Commit**

```bash
git add apps/accounts/views.py apps/accounts/urls.py apps/accounts/tests.py
git commit -m "feat: add user management views and URLs"
```

---

## Task 3: Templates + Sidebar

**Files:**
- Create: `templates/accounts/user_list.html`
- Create: `templates/accounts/user_form.html`
- Create: `templates/accounts/user_detail.html`
- Create: `templates/accounts/user_password.html`
- Create: `templates/accounts/user_confirm_delete.html`
- Modify: `templates/partials/sidebar.html`

No automated tests — verified visually via the running app.

- [ ] **Step 1: Create `templates/accounts/user_list.html`**

```html
{% extends "base.html" %}
{% load i18n %}

{% block title %}{% trans "Benutzerverwaltung" %}{% endblock %}
{% block page_title %}{% trans "Benutzerverwaltung" %}{% endblock %}

{% block header_actions %}
  <a href="{% url 'accounts:user-create' %}" class="btn-primary">
    <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
      <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
    </svg>
    {% trans "Neuer Benutzer" %}
  </a>
{% endblock %}

{% block content %}
  {% if messages %}
    {% for message in messages %}
      <div class="mb-4 px-4 py-3 rounded border border-status-success/40 bg-status-success-bg text-sm text-status-success">
        {{ message }}
      </div>
    {% endfor %}
  {% endif %}

  <div class="overflow-x-auto rounded border border-border">
    <table class="data-table">
      <thead>
        <tr>
          <th>{% trans "Benutzername" %}</th>
          <th class="hidden md:table-cell">{% trans "Name" %}</th>
          <th class="hidden md:table-cell">{% trans "E-Mail" %}</th>
          <th>{% trans "Rolle" %}</th>
          <th>{% trans "Status" %}</th>
          <th class="w-32"></th>
        </tr>
      </thead>
      <tbody>
        {% for u in users %}
        <tr>
          <td class="font-medium">
            <a href="{% url 'accounts:user-detail' u.pk %}" class="hover:text-content-primary transition-colors">
              {{ u.username }}
            </a>
          </td>
          <td class="text-sm text-content-secondary hidden md:table-cell">
            {{ u.get_full_name|default:"—" }}
          </td>
          <td class="text-sm text-content-secondary hidden md:table-cell">
            {{ u.email|default:"—" }}
          </td>
          <td>
            <span class="badge badge-neutral">{{ u.role|default:"—" }}</span>
          </td>
          <td>
            {% if u.is_active %}
              <span class="badge badge-success">{% trans "Aktiv" %}</span>
            {% else %}
              <span class="badge badge-neutral">{% trans "Inaktiv" %}</span>
            {% endif %}
          </td>
          <td>
            <div class="flex items-center gap-2 justify-end">
              <a href="{% url 'accounts:user-update' u.pk %}"
                 class="text-xs text-content-tertiary hover:text-content-primary transition-colors px-2 py-1 rounded hover:bg-surface-card">
                {% trans "Bearbeiten" %}
              </a>
              <form method="post" action="{% url 'accounts:user-toggle-active' u.pk %}">
                {% csrf_token %}
                <button type="submit"
                  class="text-xs text-content-tertiary hover:text-content-primary transition-colors px-2 py-1 rounded hover:bg-surface-card">
                  {% if u.is_active %}{% trans "Deaktivieren" %}{% else %}{% trans "Aktivieren" %}{% endif %}
                </button>
              </form>
            </div>
          </td>
        </tr>
        {% empty %}
        <tr>
          <td colspan="6" class="text-center py-8 text-sm text-content-tertiary">
            {% trans "Keine Benutzer gefunden." %}
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
{% endblock %}
```

- [ ] **Step 2: Create `templates/accounts/user_form.html`**

```html
{% extends "base.html" %}
{% load i18n %}

{% block title %}{{ form_title }}{% endblock %}
{% block page_title %}{{ form_title }}{% endblock %}

{% block header_actions %}
  <a href="{% url 'accounts:user-list' %}" class="btn-ghost">
    {% trans "Abbrechen" %}
  </a>
{% endblock %}

{% block content %}
  <div class="max-w-2xl">
    <div class="card p-6">
      <form method="post" novalidate>
        {% csrf_token %}

        <div class="space-y-5">

          {% if form.non_field_errors %}
            <div class="border border-status-danger/40 bg-status-danger-bg rounded px-4 py-3 text-sm text-status-danger">
              {% for error in form.non_field_errors %}{{ error }}{% endfor %}
            </div>
          {% endif %}

          {# ── Benutzerdaten ───────────────────────────────────────── #}
          <div class="pt-2">
            <p class="text-2xs text-content-tertiary uppercase tracking-wider font-medium mb-4">
              {% trans "Benutzerdaten" %}
            </p>
            <div class="space-y-5">

              <div>
                <label class="text-2xs text-content-tertiary uppercase tracking-wider font-medium block mb-1.5">
                  {{ form.username.label }} <span class="text-status-danger">*</span>
                </label>
                {{ form.username }}
                {% if form.username.errors %}
                  <p class="mt-1 text-xs text-status-danger">{{ form.username.errors.0 }}</p>
                {% endif %}
              </div>

              <div>
                <label class="text-2xs text-content-tertiary uppercase tracking-wider font-medium block mb-1.5">
                  {{ form.first_name.label }}
                </label>
                {{ form.first_name }}
              </div>

              <div>
                <label class="text-2xs text-content-tertiary uppercase tracking-wider font-medium block mb-1.5">
                  {{ form.last_name.label }}
                </label>
                {{ form.last_name }}
              </div>

              <div>
                <label class="text-2xs text-content-tertiary uppercase tracking-wider font-medium block mb-1.5">
                  {{ form.email.label }}
                </label>
                {{ form.email }}
                {% if form.email.errors %}
                  <p class="mt-1 text-xs text-status-danger">{{ form.email.errors.0 }}</p>
                {% endif %}
              </div>

            </div>
          </div>

          {# ── Zugang ──────────────────────────────────────────────── #}
          <div class="pt-2 border-t border-border">
            <p class="text-2xs text-content-tertiary uppercase tracking-wider font-medium mb-4">
              {% trans "Zugang" %}
            </p>
            <div class="space-y-5">

              <div>
                <label class="text-2xs text-content-tertiary uppercase tracking-wider font-medium block mb-1.5">
                  {{ form.role.label }} <span class="text-status-danger">*</span>
                </label>
                {{ form.role }}
                {% if form.role.errors %}
                  <p class="mt-1 text-xs text-status-danger">{{ form.role.errors.0 }}</p>
                {% endif %}
              </div>

              {% if form.is_active %}
              <div class="flex items-center gap-3">
                {{ form.is_active }}
                <label class="text-sm text-content-secondary">{{ form.is_active.label }}</label>
              </div>
              {% endif %}

              {% if form.password1 %}
              <div>
                <label class="text-2xs text-content-tertiary uppercase tracking-wider font-medium block mb-1.5">
                  {{ form.password1.label }} <span class="text-status-danger">*</span>
                </label>
                {{ form.password1 }}
              </div>
              <div>
                <label class="text-2xs text-content-tertiary uppercase tracking-wider font-medium block mb-1.5">
                  {{ form.password2.label }} <span class="text-status-danger">*</span>
                </label>
                {{ form.password2 }}
                {% if form.password2.errors %}
                  <p class="mt-1 text-xs text-status-danger">{{ form.password2.errors.0 }}</p>
                {% endif %}
              </div>
              {% endif %}

            </div>
          </div>

        </div>

        <div class="flex items-center gap-3 mt-7 pt-5 border-t border-border">
          <button type="submit" class="btn-primary">{{ submit_label }}</button>
          <a href="{% url 'accounts:user-list' %}" class="text-sm text-content-tertiary hover:text-content-primary transition-colors">
            {% trans "Abbrechen" %}
          </a>
        </div>

      </form>
    </div>
  </div>
{% endblock %}
```

- [ ] **Step 3: Create `templates/accounts/user_detail.html`**

```html
{% extends "base.html" %}
{% load i18n %}

{% block title %}{{ target_user.username }}{% endblock %}
{% block page_title %}{{ target_user.username }}{% endblock %}

{% block header_actions %}
  <a href="{% url 'accounts:user-update' target_user.pk %}" class="btn-ghost">
    <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
      <path stroke-linecap="round" stroke-linejoin="round"
        d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L10.582 16.07a4.5 4.5 0 0 1-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 0 1 1.13-1.897l8.932-8.931Zm0 0L19.5 7.125" />
    </svg>
    {% trans "Bearbeiten" %}
  </a>
  <a href="{% url 'accounts:user-list' %}" class="btn-ghost">
    ← {% trans "Zurück" %}
  </a>
{% endblock %}

{% block content %}
  {% if messages %}
    {% for message in messages %}
      <div class="mb-4 px-4 py-3 rounded border border-status-success/40 bg-status-success-bg text-sm text-status-success">
        {{ message }}
      </div>
    {% endfor %}
  {% endif %}

  <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">

    {# ── Main info card ────────────────────────────────────────────── #}
    <div class="lg:col-span-2 card p-6 space-y-5">

      <div class="flex items-start justify-between gap-4">
        <h2 class="text-lg font-semibold text-content-primary">{{ target_user.username }}</h2>
        {% if target_user.is_active %}
          <span class="badge badge-success shrink-0">{% trans "Aktiv" %}</span>
        {% else %}
          <span class="badge badge-neutral shrink-0">{% trans "Inaktiv" %}</span>
        {% endif %}
      </div>

      <dl class="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-4">
        <div>
          <dt class="text-2xs text-content-tertiary uppercase tracking-wider font-medium mb-1">{% trans "Vorname" %}</dt>
          <dd class="text-sm text-content-primary">{{ target_user.first_name|default:"—" }}</dd>
        </div>
        <div>
          <dt class="text-2xs text-content-tertiary uppercase tracking-wider font-medium mb-1">{% trans "Nachname" %}</dt>
          <dd class="text-sm text-content-primary">{{ target_user.last_name|default:"—" }}</dd>
        </div>
        <div>
          <dt class="text-2xs text-content-tertiary uppercase tracking-wider font-medium mb-1">{% trans "E-Mail" %}</dt>
          <dd class="text-sm text-content-primary">{{ target_user.email|default:"—" }}</dd>
        </div>
        <div>
          <dt class="text-2xs text-content-tertiary uppercase tracking-wider font-medium mb-1">{% trans "Rolle" %}</dt>
          <dd><span class="badge badge-neutral">{{ target_user.role|default:"—" }}</span></dd>
        </div>
        <div>
          <dt class="text-2xs text-content-tertiary uppercase tracking-wider font-medium mb-1">{% trans "Passwort zuletzt geändert" %}</dt>
          <dd class="text-sm font-mono text-content-secondary">{{ target_user.password_changed_at|date:"Y-m-d H:i" }}</dd>
        </div>
      </dl>

    </div>

    {# ── Actions card ──────────────────────────────────────────────── #}
    <div class="card p-5 space-y-3">
      <h3 class="text-xs font-medium text-content-secondary uppercase tracking-wider">
        {% trans "Aktionen" %}
      </h3>

      <a href="{% url 'accounts:user-password' target_user.pk %}"
         class="block w-full text-center px-3 py-2 text-xs border border-border rounded text-content-secondary hover:bg-surface-card hover:text-content-primary transition-colors">
        {% trans "Passwort setzen" %}
      </a>

      <form method="post" action="{% url 'accounts:user-toggle-active' target_user.pk %}">
        {% csrf_token %}
        <button type="submit"
          class="block w-full text-center px-3 py-2 text-xs border border-border rounded text-content-secondary hover:bg-surface-card hover:text-content-primary transition-colors">
          {% if target_user.is_active %}{% trans "Deaktivieren" %}{% else %}{% trans "Aktivieren" %}{% endif %}
        </button>
      </form>

      <a href="{% url 'accounts:user-delete' target_user.pk %}"
         class="block w-full text-center px-3 py-2 text-xs border border-status-danger/30 rounded text-status-danger hover:bg-status-danger-bg transition-colors">
        {% trans "Löschen" %}
      </a>

      <dl class="pt-3 border-t border-border space-y-3">
        <div>
          <dt class="text-2xs text-content-tertiary uppercase tracking-wider font-medium mb-1">{% trans "Erstellt am" %}</dt>
          <dd class="font-mono text-xs text-content-secondary">{{ target_user.date_joined|date:"Y-m-d" }}</dd>
        </div>
        <div>
          <dt class="text-2xs text-content-tertiary uppercase tracking-wider font-medium mb-1">{% trans "ID" %}</dt>
          <dd class="font-mono text-xs text-content-tertiary">#{{ target_user.pk }}</dd>
        </div>
      </dl>
    </div>

  </div>
{% endblock %}
```

- [ ] **Step 4: Create `templates/accounts/user_password.html`**

```html
{% extends "base.html" %}
{% load i18n %}

{% block title %}{% trans "Passwort setzen" %}{% endblock %}
{% block page_title %}{% trans "Passwort setzen" %}{% endblock %}

{% block header_actions %}
  <a href="{% url 'accounts:user-detail' target_user.pk %}" class="btn-ghost">
    {% trans "Abbrechen" %}
  </a>
{% endblock %}

{% block content %}
  <div class="max-w-2xl">
    <div class="card p-6">

      <p class="text-sm text-content-secondary mb-6">
        {% blocktrans with username=target_user.username %}
          Neues Passwort für <strong>{{ username }}</strong> setzen.
          Das 90-Tage-Passwort-Limit wird zurückgesetzt.
        {% endblocktrans %}
      </p>

      <form method="post" novalidate>
        {% csrf_token %}

        <div class="space-y-5">

          {% if form.non_field_errors %}
            <div class="border border-status-danger/40 bg-status-danger-bg rounded px-4 py-3 text-sm text-status-danger">
              {% for error in form.non_field_errors %}{{ error }}{% endfor %}
            </div>
          {% endif %}

          <div>
            <label class="text-2xs text-content-tertiary uppercase tracking-wider font-medium block mb-1.5">
              {{ form.new_password1.label }} <span class="text-status-danger">*</span>
            </label>
            {{ form.new_password1 }}
          </div>

          <div>
            <label class="text-2xs text-content-tertiary uppercase tracking-wider font-medium block mb-1.5">
              {{ form.new_password2.label }} <span class="text-status-danger">*</span>
            </label>
            {{ form.new_password2 }}
            {% if form.new_password2.errors %}
              <p class="mt-1 text-xs text-status-danger">{{ form.new_password2.errors.0 }}</p>
            {% endif %}
          </div>

        </div>

        <div class="flex items-center gap-3 mt-7 pt-5 border-t border-border">
          <button type="submit" class="btn-primary">{% trans "Passwort setzen" %}</button>
          <a href="{% url 'accounts:user-detail' target_user.pk %}"
             class="text-sm text-content-tertiary hover:text-content-primary transition-colors">
            {% trans "Abbrechen" %}
          </a>
        </div>

      </form>
    </div>
  </div>
{% endblock %}
```

- [ ] **Step 5: Create `templates/accounts/user_confirm_delete.html`**

```html
{% extends "base.html" %}
{% load i18n %}

{% block title %}{% trans "Benutzer löschen" %}{% endblock %}
{% block page_title %}{% trans "Benutzer löschen" %}{% endblock %}

{% block header_actions %}
  <a href="{% url 'accounts:user-detail' target_user.pk %}" class="btn-ghost">
    {% trans "Abbrechen" %}
  </a>
{% endblock %}

{% block content %}
  <div class="max-w-2xl">
    <div class="card p-6">

      {% if has_audit_entries %}

        <div class="border border-status-danger/40 bg-status-danger-bg rounded px-4 py-3 text-sm text-status-danger mb-6">
          {% blocktrans with username=target_user.username %}
            <strong>{{ username }}</strong> hat Audit-Einträge und kann nicht gelöscht werden.
            GMP-konforme Alternative: Benutzer deaktivieren.
          {% endblocktrans %}
        </div>

        <div class="flex items-center gap-3">
          <form method="post" action="{% url 'accounts:user-toggle-active' target_user.pk %}">
            {% csrf_token %}
            <button type="submit" class="btn-primary">
              {% trans "Stattdessen deaktivieren" %}
            </button>
          </form>
          <a href="{% url 'accounts:user-detail' target_user.pk %}"
             class="text-sm text-content-tertiary hover:text-content-primary transition-colors">
            {% trans "Abbrechen" %}
          </a>
        </div>

      {% else %}

        <p class="text-sm text-content-secondary mb-6">
          {% blocktrans with username=target_user.username %}
            Benutzer <strong>{{ username }}</strong> unwiderruflich löschen?
          {% endblocktrans %}
        </p>

        <div class="flex items-center gap-3">
          <form method="post">
            {% csrf_token %}
            <button type="submit"
              class="px-3 py-1.5 text-xs border border-status-danger/30 rounded text-status-danger hover:bg-status-danger-bg transition-colors">
              {% trans "Endgültig löschen" %}
            </button>
          </form>
          <a href="{% url 'accounts:user-detail' target_user.pk %}"
             class="text-sm text-content-tertiary hover:text-content-primary transition-colors">
            {% trans "Abbrechen" %}
          </a>
        </div>

      {% endif %}

    </div>
  </div>
{% endblock %}
```

- [ ] **Step 6: Update `templates/partials/sidebar.html`**

Change the placeholder `href="#"` on the "Benutzer" nav item:

```html
  <a href="{% url 'accounts:user-list' %}"
     class="nav-item {% if request.resolver_match.app_name == 'accounts' and request.resolver_match.url_name == 'user-list' %}active{% endif %}">
```

- [ ] **Step 7: Run full test suite**

```bash
docker compose exec web python manage.py test -v 2 2>&1 | tail -8
```

Expected: OK (all tests pass)

- [ ] **Step 8: Verify visually**

Open http://localhost:8000, log in as Admin and check:
1. Sidebar "Benutzer"-Link führt zur Liste
2. Neuer Benutzer anlegen → Rolle wird korrekt gesetzt
3. Benutzer bearbeiten → Rolle, E-Mail änderbar
4. Passwort setzen → Login mit neuem Passwort funktioniert
5. Deaktivieren → Benutzer erscheint als Inaktiv in der Liste
6. Löschen ohne Audit-Einträge → User weg
7. Löschen mit Audit-Einträgen → Fehlermeldung + Deaktivieren-Button

- [ ] **Step 9: Commit**

```bash
git add templates/accounts/user_list.html templates/accounts/user_form.html templates/accounts/user_detail.html templates/accounts/user_password.html templates/accounts/user_confirm_delete.html templates/partials/sidebar.html
git commit -m "feat: add user management templates and wire sidebar link"
```
