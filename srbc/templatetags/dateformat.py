from datetime import date
from django import template

register = template.Library()

@register.filter
def dateformat(date: date ):
    return date.strftime('%Y-%m-%d')