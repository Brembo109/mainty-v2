"""
Build filter chip data for the Linear-style toolbar.

Each list view defines its filter dimensions and hands them, together with
the request and bound filter form, to `build_toolbar_context()`. The result
is unpacked into the template context and consumed by `_filter_toolbar.html`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable
from urllib.parse import urlencode

from django.forms import Form
from django.http import HttpRequest


@dataclass
class FilterDimension:
    """One filterable dimension (e.g. 'Status' or 'Standort')."""
    key: str
    label: str
    hint: str | None = None
    display_map: dict | None = None


def build_active_chips(
    request: HttpRequest,
    form: Form,
    dimensions: Iterable[FilterDimension],
) -> list[dict[str, Any]]:
    """
    Return a list of active-filter chip dicts.

    For multi-value params (e.g. ?status=frei&status=gesperrt), the chip
    shows the first value as text and '+N' for the rest.
    """
    chips: list[dict[str, Any]] = []
    get = request.GET

    for dim in dimensions:
        raw_values = [v for v in get.getlist(dim.key) if v != ""]
        if not raw_values:
            continue

        display_values = [_display_for(dim, form, v) for v in raw_values]

        chips.append({
            "key": dim.key,
            "label": dim.label,
            "value_display": display_values[0],
            "extra_count": len(display_values) - 1,
            "remove_url": _url_without_param(request, dim.key),
        })

    return chips


def _display_for(dim: FilterDimension, form: Form, raw: str) -> str:
    """Resolve the display label for a raw GET value."""
    if dim.display_map and raw in dim.display_map:
        return dim.display_map[raw]

    field_obj = form.fields.get(dim.key)
    if field_obj is not None and hasattr(field_obj, "choices"):
        for value, label in field_obj.choices:
            if str(value) == raw:
                return str(label)

    return raw


def _url_without_param(request: HttpRequest, param: str) -> str:
    """Return current URL minus all instances of `param`."""
    params = request.GET.copy()
    # QueryDict.pop removes all entries for the key
    params.pop(param, None)
    # Never carry pagination through a filter change
    params.pop("page", None)
    query = urlencode(params, doseq=True)
    return f"{request.path}?{query}" if query else request.path


def build_toolbar_context(
    request: HttpRequest,
    form: Form,
    dimensions: Iterable[FilterDimension],
    *,
    search_name: str = "q",
    search_placeholder: str = "Suche…",
    hx_target: str,
    list_url: str | None = None,
    inline_fields: Iterable[str] | None = None,
) -> dict[str, Any]:
    """
    Build the complete context dict the toolbar partial expects.
    Unpack the result into your template context.
    """
    dimensions = list(dimensions)
    return {
        "filter_form": form,
        "filter_search_name": search_name,
        "filter_search_value": request.GET.get(search_name, ""),
        "filter_search_placeholder": search_placeholder,
        "filter_dimensions": [
            {"key": d.key, "label": d.label, "hint": d.hint}
            for d in dimensions
        ],
        "filter_active_chips": build_active_chips(request, form, dimensions),
        "filter_reset_url": list_url or request.path,
        "filter_hx_target": hx_target,
        "filter_hx_url": list_url or request.path,
        "filter_inline_fields": list(inline_fields or []),
    }
