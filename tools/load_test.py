#!/usr/bin/env python3
"""Simple async load generator inspired by k6 script.

Usage:
  python tools/load_test.py

Configuration via env variables:
  BASE_URL - default http://localhost:8000
  STAGE1_DUR - seconds (default 30)
  STAGE1_VUS - int (default 50)
  STAGE2_DUR - seconds (default 60)
  STAGE2_VUS - int (default 50)
  STAGE3_DUR - seconds (default 20)

This script is intentionally simple and safe for local use. It POSTs orders and measures latency.
"""

import asyncio
import httpx
import random
import os
import time
import statistics

BASE = os.getenv("BASE_URL", "http://localhost:8000")
HEADERS = {"Content-Type": "application/json"}

# stages: (duration_seconds, target_vus)
STAGES = [
    (int(os.getenv("STAGE1_DUR", "30")), int(os.getenv("STAGE1_VUS", "50"))),
    (int(os.getenv("STAGE2_DUR", "60")), int(os.getenv("STAGE2_VUS", "50"))),
    (int(os.getenv("STAGE3_DUR", "20")), int(os.getenv("STAGE3_VUS", "0"))),
]

REQUEST_SLEEP = float(os.getenv("REQUEST_SLEEP", "0.05"))


async def vu_loop(client: httpx.AsyncClient, stop_event: asyncio.Event, latencies: list):
    while not stop_event.is_set():
        payload = {
            "symbol": random.choice(["FOO", "BAR", "BAZ"]),
            "side": "BUY" if random.random() > 0.5 else "SELL",
            "qty": 1,
            "price": 100,
        }
        start = time.perf_counter()
        try:
            r = await client.post("/orders", json=payload, headers=HEADERS, timeout=10.0)
            latency = (time.perf_counter() - start) * 1000.0
            latencies.append(latency)
        except Exception:
            latency = (time.perf_counter() - start) * 1000.0
            latencies.append(latency)
        await asyncio.sleep(REQUEST_SLEEP)


async def run_stage(target_vus: int, duration: int, metrics: dict):
    if target_vus <= 0:
        # just sleep for the duration
        await asyncio.sleep(duration)
        return

    stop_event = asyncio.Event()
    latencies = []
    async with httpx.AsyncClient(base_url=BASE) as client:
        tasks = [asyncio.create_task(vu_loop(client, stop_event, latencies)) for _ in range(target_vus)]
        await asyncio.sleep(duration)
        stop_event.set()
        await asyncio.gather(*tasks, return_exceptions=True)

    metrics.setdefault("latencies", []).extend(latencies)
    metrics.setdefault("requests", 0)
    metrics["requests"] += len(latencies)


async def main():
    metrics = {}
    for duration, target in STAGES:
        print(f"Running stage: {target} VUs for {duration}s")
        await run_stage(target, duration, metrics)

    all_lat = metrics.get("latencies", [])
    if all_lat:
        try:
            p95 = statistics.quantiles(all_lat, n=100)[94]
        except Exception:
            p95 = sorted(all_lat)[max(0, int(len(all_lat) * 0.95) - 1)]
        print(f"Requests: {metrics.get('requests', 0)}")
        print(f"P95 latency (ms): {p95:.2f}")
    else:
        print("No requests recorded.")


if __name__ == "__main__":
    asyncio.run(main())
