def join_segments(values):
    return '/'.join(v.strip() for v in values if v.strip())
