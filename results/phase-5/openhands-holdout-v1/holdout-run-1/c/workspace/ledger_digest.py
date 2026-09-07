def ledger_digest(entries):
    totals = {}
    for entry in entries:
        account = entry['account']
        totals[account] = totals.get(account, 0) + entry['delta']
    return '\n'.join(f"{account}={total}" for account, total in totals.items())
