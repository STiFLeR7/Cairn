def normalize(value):
    return value.strip()

def is_valid(value):
    return bool(value and value.strip())

def format_record(value):
    return value

def count_items(values):
    return len(list(values))

def summarize(values):
    return ''
