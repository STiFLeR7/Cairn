def normalize(value):
    return " ".join(value.split())

def is_valid(value):
    return bool(normalize(value))

def format_record(value):
    return normalize(value).title()

def count_items(values):
    return len([v for v in values if is_valid(v)])

def summarize(values):
    return ", ".join(format_record(v) for v in values if is_valid(v))
