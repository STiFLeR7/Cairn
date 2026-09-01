def normalize(value):
    return value.strip()

def is_valid(value):
    return bool(value)

def format_record(value):
    return value

def count_items(values):
    return sum(1 for _ in values)

def summarize(values):
    return ", ".join(str(v) for v in values)
