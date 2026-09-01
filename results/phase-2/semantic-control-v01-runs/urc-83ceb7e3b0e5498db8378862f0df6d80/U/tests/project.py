def is_nonempty(value):
    return bool(value)

def is_positive(value):
    return value > 0

def is_even(value):
    return value % 2 == 0

def has_prefix(value, prefix):
    return value.startswith(prefix)
