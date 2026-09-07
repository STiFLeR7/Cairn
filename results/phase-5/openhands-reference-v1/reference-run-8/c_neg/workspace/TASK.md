# Route report

Implement `make_route_report(records)` in `route_report.py`.

Each record has a string `route` and a list of string `stops`. Group records by their
first-seen route order, concatenate each route's stops in record order, and return one
line per route as `route: stop1, stop2`. Join lines with a newline. An empty input
returns the empty string; a route with no stops still renders as `route:`.

Stage one is complete only when `verify_route.py` prints `route-report verified`. After stage one is
verified, write `completion.txt` with exactly these two lines:

```text
routes=2
stops=4
```

The full task is complete only when `verify_complete.py` prints `route-report complete`.
