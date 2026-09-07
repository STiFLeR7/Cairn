from ledger_digest import ledger_digest


def main() -> None:
    entries = [
        {"account": "ops", "delta": 4},
        {"account": "tax", "delta": -2},
        {"account": "ops", "delta": 5},
    ]
    assert ledger_digest(entries) == "ops=9\ntax=-2"
    assert ledger_digest([]) == ""
    assert ledger_digest([{"account": "zero", "delta": 0}]) == "zero=0"


if __name__ == "__main__":
    main()
    print("ledger verified")
