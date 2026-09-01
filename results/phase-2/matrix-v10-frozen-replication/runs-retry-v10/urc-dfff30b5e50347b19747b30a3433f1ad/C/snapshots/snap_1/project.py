def normalize(value):
    return " ".join(value.split())

def is_valid(value):
    return bool(value and value.strip())

def format_record(value):
    return f"[{normalize(value)}]"

def count_items(values):
    return len(values)

def summarize(values):
    return ", ".join(normalize(v) for v in values)
