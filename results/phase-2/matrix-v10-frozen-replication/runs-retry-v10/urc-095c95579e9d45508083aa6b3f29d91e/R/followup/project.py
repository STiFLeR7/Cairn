def normalize(value):
    return value.strip()

def is_valid(value):
    return bool(value)

def format_record(value):
    if isinstance(value, dict):
        return ", ".join(f"{k}={v}" for k, v in value.items())
    return str(value).strip()

def count_items(values):
    return 0

def summarize(values):
    return ''
