from django.contrib.auth.models import Group
from django.core import mail
from django.test import TestCase, Client, override_settings
from django.urls import reverse

from apps.accounts.constants import Role
from apps.accounts.models import User
from apps.core.models import SiteConfig


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
        self.assertEqual(response.status_code, 409)
        self.assertTrue(User.objects.filter(username="audited").exists())

    def test_blocked_delete_shows_deactivate_button(self):
        target = User.objects.create_user(username="audited2", password="pass")
        AuditLog.objects.create(actor=target, actor_username="audited2", action="CREATE")
        response = self.client.post(reverse("accounts:user-delete", kwargs={"pk": target.pk}))
        self.assertContains(response, "toggle-active", status_code=409)


class PasswordResetFromEmailTest(TestCase):
    def setUp(self):
        self.client = Client()

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_password_reset_uses_siteconfig_from_email(self):
        SiteConfig.objects.create(pk=1, email_from="noreply@mycompany.com")
        User.objects.create_user(
            username="resetuser", email="resetuser@test.com", password="pass123"
        )
        self.client.post(
            reverse("accounts:password_reset"), {"email": "resetuser@test.com"}
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].from_email, "noreply@mycompany.com")
