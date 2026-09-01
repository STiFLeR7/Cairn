def is_nonempty(value):
    return bool(value)

def is_positive(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0

def is_even(value):
    return isinstance(value, int) and not isinstance(value, bool) and value % 2 == 0

def has_prefix(value, prefix):
    return isinstance(value, str) and isinstance(prefix, str) and value.startswith(prefix)
