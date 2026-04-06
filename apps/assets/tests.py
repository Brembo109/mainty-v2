from django.test import TestCase

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
