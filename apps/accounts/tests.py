from django.contrib.auth.models import Group
from django.test import TestCase, Client
from django.urls import reverse

from apps.accounts.constants import Role
from apps.accounts.models import User


class UserThemeDefaultTest(TestCase):
    def test_theme_defaults_to_dark(self):
        user = User.objects.create_user(username="testuser", password="testpass123")
        self.assertEqual(user.theme, "dark")

    def test_theme_can_be_set_to_light(self):
        user = User.objects.create_user(username="testuser2", password="testpass123")
        user.theme = "light"
        user.save(update_fields=["theme"])
        user.refresh_from_db()
        self.assertEqual(user.theme, "light")


class SetThemeViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="themeuser", password="testpass123")
        self.client.force_login(self.user)

    def test_set_theme_to_light(self):
        response = self.client.post(
            reverse("accounts:set_theme"),
            {"theme": "light", "next": "/"},
        )
        self.assertRedirects(response, "/", fetch_redirect_response=False)
        self.user.refresh_from_db()
        self.assertEqual(self.user.theme, "light")

    def test_set_theme_to_dark(self):
        self.user.theme = "light"
        self.user.save(update_fields=["theme"])
        response = self.client.post(
            reverse("accounts:set_theme"),
            {"theme": "dark", "next": "/"},
        )
        self.assertRedirects(response, "/", fetch_redirect_response=False)
        self.user.refresh_from_db()
        self.assertEqual(self.user.theme, "dark")

    def test_invalid_theme_ignored(self):
        self.user.theme = "dark"
        self.user.save(update_fields=["theme"])
        self.client.post(
            reverse("accounts:set_theme"),
            {"theme": "rainbow", "next": "/"},
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.theme, "dark")  # unchanged

    def test_requires_login(self):
        self.client.logout()
        response = self.client.post(
            reverse("accounts:set_theme"),
            {"theme": "light", "next": "/"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response["Location"])

    def test_next_open_redirect_rejected(self):
        response = self.client.post(
            reverse("accounts:set_theme"),
            {"theme": "light", "next": "https://evil.com"},
        )
        self.assertRedirects(response, "/", fetch_redirect_response=False)

    def test_get_returns_405(self):
        response = self.client.get(reverse("accounts:set_theme"))
        self.assertEqual(response.status_code, 405)


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
