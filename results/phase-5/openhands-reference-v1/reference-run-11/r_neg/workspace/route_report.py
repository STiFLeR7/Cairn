def make_route_report(records):
    grouped = {}
    for record in records:
        grouped.setdefault(record['route'], []).extend(record['stops'])
    return '\n'.join(f"{route}:{' ' + ', '.join(stops) if stops else ''}" for route, stops in grouped.items())
