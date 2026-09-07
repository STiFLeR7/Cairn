from pathlib import Path

from verify_ledger import main as verify_ledger


def main() -> None:
    verify_ledger()
    assert Path("audit.txt").read_text(encoding="utf-8") == "accounts=2\nnet=7\n"


if __name__ == "__main__":
    main()
    print("ledger complete")
