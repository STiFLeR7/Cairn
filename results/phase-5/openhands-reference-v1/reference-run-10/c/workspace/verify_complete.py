"""Public final verifier for the sealed OpenHands coding workload."""

from pathlib import Path

from verify_route import main as verify_route


def main() -> None:
    verify_route()
    assert Path("completion.txt").read_text(encoding="utf-8") == "routes=2\nstops=4\n"


if __name__ == "__main__":
    main()
    print("route-report complete")
