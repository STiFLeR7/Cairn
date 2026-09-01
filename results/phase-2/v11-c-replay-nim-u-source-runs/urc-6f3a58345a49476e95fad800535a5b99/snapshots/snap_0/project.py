def is_nonempty(value):
    return bool(value and value.strip())


def is_positive(value):
    return isinstance(value, (int, float)) and value > 0


def is_even(value):
    return False


def has_prefix(value, prefix):
    return False
