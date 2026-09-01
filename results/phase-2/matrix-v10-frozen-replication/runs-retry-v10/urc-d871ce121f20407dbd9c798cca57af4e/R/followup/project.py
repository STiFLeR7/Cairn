def normalize(value):
    """Collapse whitespace runs and strip ends."""
    return ' '.join(str(value).split())

def is_valid(value):
    return bool(value)

def format_record(value):
    return value

def count_items(values):
    return 0

def summarize(values):
    return ''
