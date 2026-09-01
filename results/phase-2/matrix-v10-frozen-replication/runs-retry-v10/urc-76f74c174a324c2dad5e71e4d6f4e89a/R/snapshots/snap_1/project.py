def normalize(value):
    return " ".join(value.split())

def is_valid(value):
    return bool(normalize(value))

def format_record(value):
    return f'record:{normalize(value)}'

def count_items(values):
    return len(values)

def summarize(values):
    return ', '.join(normalize(v) for v in values)
