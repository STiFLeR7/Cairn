import re

def normalize(value):
    return re.sub(r"\s+", " ", value).strip()

def is_valid(value):
    return bool(value)

def format_record(value):
    return value

def count_items(values):
    return 0

def summarize(values):
    return ''
