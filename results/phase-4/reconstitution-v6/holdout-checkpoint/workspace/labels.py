import re


def normalize_label(value):
    return re.sub(r'\s+', '-', value.strip()).lower()
