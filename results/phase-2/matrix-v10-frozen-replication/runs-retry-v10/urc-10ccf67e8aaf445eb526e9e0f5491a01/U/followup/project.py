def normalize(value):
    return value.strip()

def is_valid(value):
    return bool(normalize(value))

def format_record(value):
    return normalize(value).title()

def count_items(values):
    return 0

def summarize(values):
    return ''
