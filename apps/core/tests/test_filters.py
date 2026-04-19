from django import forms
from django.test import RequestFactory, TestCase

from apps.core.filters import (
    FilterDimension,
    build_active_chips,
    build_toolbar_context,
)


class FakeFilterForm(forms.Form):
    q = forms.CharField(required=False)
    status = forms.MultipleChoiceField(
        choices=[
            ("frei", "Frei"),
            ("gesperrt", "Gesperrt"),
            ("wartung", "In Wartung"),
        ],
        required=False,
    )
    location = forms.CharField(required=False)


DIMENSIONS = [
    FilterDimension("status", "Status"),
    FilterDimension("location", "Standort"),
]


class BuildActiveChipsTests(TestCase):
    def setUp(self):
        self.rf = RequestFactory()

    def test_empty_querystring_returns_no_chips(self):
        request = self.rf.get("/assets/")
        form = FakeFilterForm(request.GET)
        self.assertEqual(build_active_chips(request, form, DIMENSIONS), [])

    def test_single_value_chip(self):
        request = self.rf.get("/assets/?status=frei")
        form = FakeFilterForm(request.GET)
        chips = build_active_chips(request, form, DIMENSIONS)
        self.assertEqual(len(chips), 1)
        chip = chips[0]
        self.assertEqual(chip["key"], "status")
        self.assertEqual(chip["label"], "Status")
        self.assertEqual(chip["value_display"], "Frei")
        self.assertEqual(chip["extra_count"], 0)
        self.assertEqual(chip["remove_url"], "/assets/")

    def test_multi_value_chip_shows_extra_count(self):
        request = self.rf.get("/assets/?status=frei&status=gesperrt")
        form = FakeFilterForm(request.GET)
        chips = build_active_chips(request, form, DIMENSIONS)
        self.assertEqual(len(chips), 1)
        self.assertEqual(chips[0]["value_display"], "Frei")
        self.assertEqual(chips[0]["extra_count"], 1)

    def test_remove_url_preserves_other_params(self):
        request = self.rf.get(
            "/assets/?status=frei&location=halle-a&q=hplc"
        )
        form = FakeFilterForm(request.GET)
        chips = build_active_chips(request, form, DIMENSIONS)
        status_chip = next(c for c in chips if c["key"] == "status")
        self.assertIn("location=halle-a", status_chip["remove_url"])
        self.assertIn("q=hplc", status_chip["remove_url"])
        self.assertNotIn("status=", status_chip["remove_url"])

    def test_remove_url_drops_pagination(self):
        request = self.rf.get("/assets/?status=frei&page=3")
        form = FakeFilterForm(request.GET)
        chips = build_active_chips(request, form, DIMENSIONS)
        self.assertNotIn("page=", chips[0]["remove_url"])

    def test_empty_value_is_ignored(self):
        request = self.rf.get("/assets/?status=")
        form = FakeFilterForm(request.GET)
        self.assertEqual(build_active_chips(request, form, DIMENSIONS), [])

    def test_display_map_overrides_choices(self):
        dim = FilterDimension(
            "has_contract", "Vertrag",
            display_map={"yes": "Vorhanden", "no": "Fehlt"},
        )
        request = self.rf.get("/assets/?has_contract=yes")
        form = FakeFilterForm(request.GET)
        chips = build_active_chips(request, form, [dim])
        self.assertEqual(chips[0]["value_display"], "Vorhanden")

    def test_raw_value_fallback_when_no_choices(self):
        request = self.rf.get("/assets/?location=Halle+A")
        form = FakeFilterForm(request.GET)
        chips = build_active_chips(request, form, DIMENSIONS)
        loc_chip = next(c for c in chips if c["key"] == "location")
        self.assertEqual(loc_chip["value_display"], "Halle A")

    def test_dimensions_with_no_matching_form_field(self):
        """If a dimension key has no form field, raw value is still shown."""
        dim = FilterDimension("made_up", "Made up")
        request = self.rf.get("/x/?made_up=something")
        form = FakeFilterForm(request.GET)
        chips = build_active_chips(request, form, [dim])
        self.assertEqual(chips[0]["value_display"], "something")


class BuildToolbarContextTests(TestCase):
    def setUp(self):
        self.rf = RequestFactory()

    def test_minimal_context(self):
        request = self.rf.get("/assets/?q=hplc")
        form = FakeFilterForm(request.GET)
        ctx = build_toolbar_context(
            request, form, DIMENSIONS,
            hx_target="#asset-results",
        )
        self.assertEqual(ctx["filter_search_value"], "hplc")
        self.assertEqual(ctx["filter_hx_target"], "#asset-results")
        self.assertEqual(ctx["filter_reset_url"], "/assets/")
        self.assertEqual(len(ctx["filter_dimensions"]), 2)
        self.assertEqual(ctx["filter_active_chips"], [])
        self.assertIs(ctx["filter_form"], form)
        self.assertEqual(ctx["filter_inline_fields"], [])

    def test_list_url_overrides_request_path(self):
        request = self.rf.get("/assets/?q=hplc&page=2")
        form = FakeFilterForm(request.GET)
        ctx = build_toolbar_context(
            request, form, DIMENSIONS,
            hx_target="#x", list_url="/assets/",
        )
        self.assertEqual(ctx["filter_reset_url"], "/assets/")
        self.assertEqual(ctx["filter_hx_url"], "/assets/")

    def test_inline_fields_are_passed_through(self):
        request = self.rf.get("/assets/")
        form = FakeFilterForm(request.GET)
        ctx = build_toolbar_context(
            request, form, DIMENSIONS,
            hx_target="#x",
            inline_fields=["status"],
        )
        self.assertEqual(ctx["filter_inline_fields"], ["status"])
