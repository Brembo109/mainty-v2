from django import template

register = template.Library()


@register.filter
def available_dimensions(dimensions, active_chips):
    """Return dimensions whose key is not in the active chips list."""
    active_keys = {chip["key"] for chip in active_chips}
    return [d for d in dimensions if d["key"] not in active_keys]


@register.filter
def get_multi_values(bound_field):
    """Yield all values of a bound field — handles single and multi-valued fields."""
    value = bound_field.value()
    if value is None or value == "":
        return []
    if isinstance(value, (list, tuple)):
        return [v for v in value if v not in (None, "")]
    return [value]
