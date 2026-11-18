
from collections import defaultdict


TIMINGS = defaultdict(lambda: {
    "calls": 0,
    "total": 0.0,
    "max": 0.0
})


def record_time(name, elapsed):

    item = TIMINGS[name]

    item["calls"] += 1
    item["total"] += elapsed
    item["max"] = max(item["max"], elapsed)


def print_timing_summary():

    print("\n================ ΧΡΟΝΟΜΕΤΡΗΣΗ ================")

    for name, item in TIMINGS.items():

        avg = (
            item["total"] / item["calls"]
            if item["calls"] else 0
        )

        print(
            f"{name:30s} "
            f"κλήσεις: {item['calls']:7d} | "
            f"σύνολο: {item['total']:10.2f}s | "
            f"μέσος: {avg:8.4f}s | "
            f"μέγιστος: {item['max']:8.4f}s"
        )
