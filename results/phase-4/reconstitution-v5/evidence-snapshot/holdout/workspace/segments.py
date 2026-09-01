def join_segments(values):
    return '/'.join(value.strip() for value in values if value.strip())
