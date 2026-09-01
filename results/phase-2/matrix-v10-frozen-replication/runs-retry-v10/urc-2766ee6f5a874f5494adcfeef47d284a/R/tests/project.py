def is_nonempty(value):
    return isinstance(value, str) and len(value) > 0

def is_positive(value):
    return value > 0

def is_even(value):
    return value % 2 == 0

def has_prefix(value, prefix):
    return isinstance(value, str) and value.startswith(prefix)
