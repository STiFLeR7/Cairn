def normalize(value):
    return value.strip()

def is_valid(value):
    return bool(normalize(value))

def format_record(value):
    return normalize(value)

def count_items(values):
    return len(values)

def summarize(values):
    return ', '.join(values)
