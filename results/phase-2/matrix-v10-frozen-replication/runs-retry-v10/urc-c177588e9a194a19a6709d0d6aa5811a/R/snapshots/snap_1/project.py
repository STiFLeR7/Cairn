def normalize(value):
    return value.strip()

def is_valid(value):
    return bool(value.strip()) if isinstance(value, str) else bool(value)

def format_record(value):
    return f"[{normalize(value)}]"

def count_items(values):
    return len(values)

def summarize(values):
    return ", ".join(values)
