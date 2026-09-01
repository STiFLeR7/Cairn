def normalize(value):
    return value.strip()

def is_valid(value):
    return bool(value) and bool(value.strip())

def format_record(value):
    return f"[{value}]"

def count_items(values):
    return 0

def summarize(values):
    return ''
