def normalize(value):
    return ' '.join(str(value).split())

def is_valid(value):
    return bool(value is not None and str(value).strip())

def format_record(value):
    return value

def count_items(values):
    return 0

def summarize(values):
    return ''
