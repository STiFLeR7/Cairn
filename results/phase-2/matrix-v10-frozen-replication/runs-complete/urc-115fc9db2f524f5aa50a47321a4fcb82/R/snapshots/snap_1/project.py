def normalize(value):
    return value.strip()

def is_valid(value):
    return bool(normalize(value)) if isinstance(value, str) else value is not None

def format_record(value):
    return value

def count_items(values):
    return 0

def summarize(values):
    return ''
