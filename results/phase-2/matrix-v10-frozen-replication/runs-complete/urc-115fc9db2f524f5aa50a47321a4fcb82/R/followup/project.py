def normalize(value):
    return value.strip()

def is_valid(value):
    return bool(normalize(value)) if isinstance(value, str) else value is not None

def format_record(value):
    return '{}: {}'.format(normalize(str(value[0])), normalize(str(value[1]))) if isinstance(value, (tuple, list)) else normalize(str(value))

def count_items(values):
    return 0

def summarize(values):
    return ''
