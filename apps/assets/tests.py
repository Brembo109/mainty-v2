from django.test import Client, TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.assets.constants import Department
from apps.assets.models import Asset


def make_user(username):
    return User.objects.create_user(username=username, password="pass")


_asset_counter = 0


def make_asset(**kwargs):
    global _asset_counter
    _asset_counter += 1
    defaults = {
        "name": "Autoklav A1",
        "serial_number": f"SN-{_asset_counter:04d}",
        "location": "Halle 3",
        "device_code": f"AKL-{_asset_counter:02d}",
        "inventory_number": f"INV-2024-{_asset_counter:03d}",
        "department": Department.HERSTELLUNG,
    }
    defaults.update(kwargs)
    return Asset.objects.create(**defaults)


class AssetDepartmentFieldTest(TestCase):
    def test_department_choices_exist(self):
        self.assertEqual(len(Department.CHOICES), 3)
        values = [c[0] for c in Department.CHOICES]
        self.assertIn("herstellung", values)
        self.assertIn("qualitaetskontrolle", values)
        self.assertIn("prozessentwicklung", values)

    def test_asset_stores_department(self):
        asset = make_asset(department=Department.QUALITAETSKONTROLLE)
        asset.refresh_from_db()
        self.assertEqual(asset.department, Department.QUALITAETSKONTROLLE)


class AssetIdentificationFieldsTest(TestCase):
    def test_device_code_and_inventory_number_stored(self):
        asset = make_asset(device_code="AKL-99", inventory_number="INV-9999")
        asset.refresh_from_db()
        self.assertEqual(asset.device_code, "AKL-99")
        self.assertEqual(asset.inventory_number, "INV-9999")

    def test_service_provider_optional(self):
        asset = make_asset(service_provider="")
        asset.refresh_from_db()
        self.assertEqual(asset.service_provider, "")

    def test_service_provider_stored(self):
        asset = make_asset(service_provider="Siemens GmbH")
        asset.refresh_from_db()
        self.assertEqual(asset.service_provider, "Siemens GmbH")


class AssetResponsibilityFieldsTest(TestCase):
    def test_responsible_and_deputy_stored(self):
        responsible = make_user("responsible_user")
        deputy = make_user("deputy_user")
        asset = make_asset(responsible=responsible, deputy=deputy)
        asset.refresh_from_db()
        self.assertEqual(asset.responsible, responsible)
        self.assertEqual(asset.deputy, deputy)

    def test_responsible_set_null_on_user_delete(self):
        responsible = make_user("to_delete")
        asset = make_asset(responsible=responsible)
        responsible.delete()
        asset.refresh_from_db()
        self.assertIsNone(asset.responsible)

    def test_deputy_set_null_on_user_delete(self):
        deputy = make_user("deputy_to_delete")
        asset = make_asset(deputy=deputy)
        deputy.delete()
        asset.refresh_from_db()
        self.assertIsNone(asset.deputy)

    def test_responsible_and_deputy_can_be_null(self):
        asset = make_asset(responsible=None, deputy=None)
        asset.refresh_from_db()
        self.assertIsNone(asset.responsible)
        self.assertIsNone(asset.deputy)


from apps.assets.forms import AssetFilterForm, AssetForm


class AssetFormValidationTest(TestCase):
    def setUp(self):
        self.responsible = User.objects.create_user(username="resp", password="pass")
        self.deputy = User.objects.create_user(username="dep", password="pass")

    def _valid_data(self, **overrides):
        data = {
            "name": "Autoklav A1",
            "serial_number": "SN-001",
            "location": "Halle 3",
            "manufacturer": "",
            "status": "free",
            "device_code": "AKL-01",
            "inventory_number": "INV-001",
            "service_provider": "",
            "department": Department.HERSTELLUNG,
            "responsible": self.responsible.pk,
            "deputy": self.deputy.pk,
        }
        data.update(overrides)
        return data

    def test_valid_form(self):
        form = AssetForm(data=self._valid_data())
        self.assertTrue(form.is_valid(), form.errors)

    def test_device_code_required(self):
        form = AssetForm(data=self._valid_data(device_code=""))
        self.assertFalse(form.is_valid())
        self.assertIn("device_code", form.errors)

    def test_inventory_number_required(self):
        form = AssetForm(data=self._valid_data(inventory_number=""))
        self.assertFalse(form.is_valid())
        self.assertIn("inventory_number", form.errors)

    def test_department_required(self):
        form = AssetForm(data=self._valid_data(department=""))
        self.assertFalse(form.is_valid())
        self.assertIn("department", form.errors)

    def test_responsible_required(self):
        form = AssetForm(data=self._valid_data(responsible=""))
        self.assertFalse(form.is_valid())
        self.assertIn("responsible", form.errors)

    def test_deputy_required(self):
        form = AssetForm(data=self._valid_data(deputy=""))
        self.assertFalse(form.is_valid())
        self.assertIn("deputy", form.errors)

    def test_service_provider_optional(self):
        form = AssetForm(data=self._valid_data(service_provider=""))
        self.assertTrue(form.is_valid(), form.errors)

    def test_inactive_user_rejected_for_responsible(self):
        inactive = User.objects.create_user(username="gone", password="pass", is_active=False)
        form = AssetForm(data=self._valid_data(responsible=inactive.pk))
        self.assertFalse(form.is_valid())
        self.assertIn("responsible", form.errors)


class AssetFilterViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="viewer", password="pass")
        self.client.force_login(self.user)

        self.responsible = User.objects.create_user(username="resp", password="pass")
        self.deputy = User.objects.create_user(username="dep", password="pass")

        self.asset_h = Asset.objects.create(
            name="Anlage Herstellung",
            serial_number="SN-H01",
            location="Halle 1",
            device_code="H-01",
            inventory_number="INV-H01",
            department=Department.HERSTELLUNG,
            responsible=self.responsible,
            deputy=self.deputy,
        )
        self.asset_q = Asset.objects.create(
            name="Anlage QK",
            serial_number="SN-Q01",
            location="Halle 2",
            device_code="Q-01",
            inventory_number="INV-Q01",
            department=Department.QUALITAETSKONTROLLE,
            responsible=self.responsible,
            deputy=self.deputy,
        )

    def test_filter_by_department(self):
        response = self.client.get(
            reverse("assets:list"),
            {"department": Department.HERSTELLUNG},
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Anlage Herstellung")
        self.assertNotContains(response, "Anlage QK")

    def test_filter_by_responsible(self):
        other_resp = User.objects.create_user(username="other_resp", password="pass")
        Asset.objects.create(
            name="Anlage Andere",
            serial_number="SN-A01",
            location="Halle 3",
            device_code="A-01",
            inventory_number="INV-A01",
            department=Department.PROZESSENTWICKLUNG,
            responsible=other_resp,
            deputy=self.deputy,
        )
        response = self.client.get(
            reverse("assets:list"),
            {"responsible": self.responsible.pk},
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 200)
        # asset_h and asset_q both have responsible=self.responsible (set in setUp)
        self.assertContains(response, "Anlage Herstellung")
        self.assertContains(response, "Anlage QK")
        self.assertNotContains(response, "Anlage Andere")
