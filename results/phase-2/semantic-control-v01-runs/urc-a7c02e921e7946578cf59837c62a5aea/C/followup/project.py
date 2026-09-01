def normalize(value):
    return value.strip()

def is_valid(value):
    return bool(value)

def format_record(value):
    return f'record:{value}'

def count_items(values):
    return len(values)

def summarize(values):
    return ','.join(values)
