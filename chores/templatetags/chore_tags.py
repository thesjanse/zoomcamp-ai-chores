from django import template

from chores.utils import chore_color_class

register = template.Library()


@register.filter
def chore_color(chore):
    return chore_color_class(chore)


@register.filter
def get_item(mapping, key):
    return mapping.get(key, [])