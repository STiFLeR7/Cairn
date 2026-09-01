def normalize(value):
    return " ".join(value.split())


def is_valid(value):
    return bool(value) and bool(str(value).strip())


def format_record(value):
    return f"{normalize(str(value))}"


def count_items(values):
    return len(values) if values else 0


def summarize(values):
    return ", ".join(normalize(str(v)) for v in values if is_valid(v))
