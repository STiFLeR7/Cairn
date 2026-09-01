def normalize(value):
    return value.strip()

def is_valid(value):
    return bool(value) and bool(str(value).strip())

def format_record(value):
    return '{}: {}'.format(str(value[0]).strip(), str(value[1]).strip()) if isinstance(value, (tuple, list)) else str(value).strip()

def count_items(values):
    return 0

def summarize(values):
    return ''
