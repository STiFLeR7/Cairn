"""Public acceptance verifier for the sealed OpenHands coding workload."""

from route_report import make_route_report


def main() -> None:
    records = [
        {"route": "north", "stops": ["elm", "river"]},
        {"route": "west", "stops": ["ridge"]},
        {"route": "north", "stops": ["oak"]},
    ]
    assert make_route_report(records) == "north: elm, river, oak\nwest: ridge"
    assert make_route_report([]) == ""
    assert make_route_report([{"route": "solo", "stops": []}]) == "solo:"


if __name__ == "__main__":
    main()
    print("route-report verified")
