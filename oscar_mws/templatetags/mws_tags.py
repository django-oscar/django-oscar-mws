from django import template

from bs4 import BeautifulStoneSoup

register = template.Library()


@register.filter
def prettify_xml(value):
    return BeautifulStoneSoup(value).prettify(formatter='xml')
