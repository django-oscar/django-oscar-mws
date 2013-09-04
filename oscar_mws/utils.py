import re

FIRST_CAPITAL_PATTERN = re.compile(r'(.)([A-Z][a-z]+)')
UPPERCASE_PATTERN = re.compile('([a-z0-9])([A-Z])')


def convert_camel_case(name):
    s1 = FIRST_CAPITAL_PATTERN.sub(r'\1_\2', name)
    return UPPERCASE_PATTERN.sub(r'\1_\2', s1).lower()
