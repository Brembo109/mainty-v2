from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Allow dict[key] access in templates: {{ mydict|get_item:somevar }}"""
    return dictionary.get(key)


@register.filter
def split(value, delimiter=","):
    """Split a string: {{ "a,b,c"|split:"," }}"""
    return value.split(delimiter)
