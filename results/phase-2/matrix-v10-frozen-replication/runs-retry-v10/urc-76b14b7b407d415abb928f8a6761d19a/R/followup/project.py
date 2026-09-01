def normalize(value):
    return value.strip()

def is_valid(value):
    return bool(value and value.strip())

def format_record(value):
    return f"[{value.strip()}]"

def count_items(values):
    return len(values)

def summarize(values):
    return ", ".join(values)
