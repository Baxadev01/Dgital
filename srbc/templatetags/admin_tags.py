from django import template
from django.contrib.auth.models import Group

register = template.Library()


@register.filter(name='has_group')
def has_group(user, group_name):
    group = Group.objects.filter(name=group_name).first()
    if not group:
        return False
    return group in user.groups.all()


@register.filter(name='index')
def get_elem_by_index(obj, i):
    return obj[i]
