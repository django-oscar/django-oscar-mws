import re

from django.core.exceptions import ImproperlyConfigured

from oscar.core.loading import _pluck_classes

FIRST_CAPITAL_PATTERN = re.compile(r'(.)([A-Z][a-z]+)')
UPPERCASE_PATTERN = re.compile('([a-z0-9])([A-Z])')


def load_class(name, default=None):
    if not name:
        return None
    try:
        module_label, class_name = name.rsplit('.', 1)
    except ValueError:
        raise ImproperlyConfigured("cannot find class {0}".format(name))
    imported_module = __import__(module_label, fromlist=[class_name])
    try:
        return _pluck_classes([imported_module], [class_name])[0]
    except IndexError:
        return None


def convert_camel_case(name):
    s1 = FIRST_CAPITAL_PATTERN.sub(r'\1_\2', name)
    return UPPERCASE_PATTERN.sub(r'\1_\2', s1).lower()
