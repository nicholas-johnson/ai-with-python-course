"""
Demo: asyncio essentials — tasks, queues, timeouts, cancellation.
Run:  python module-00-python-fundamentals/demo/04_async_essentials.py
"""

import asyncio
import random


# --- Basic async/await ---

async def scan_sector(sector: str, delay: float) -> str:
    print(f"  Scanning {sector}...")
    await asyncio.sleep(delay)
    reading = round(random.uniform(0.1, 9.9), 2)
    return f"{sector}: radiation level {reading}"


async def demo_basic():
    print("\n--- Basic async/await ---")
    result = await scan_sector("Alpha-7", 0.5)
    print(f"  Result: {result}")


# --- Concurrent tasks ---

async def demo_concurrent():
    print("\n--- Concurrent tasks with gather ---")
    sectors = ["Alpha-7", "Beta-12", "Gamma-3", "Delta-9"]
    tasks = [scan_sector(s, random.uniform(0.2, 1.0)) for s in sectors]
    results = await asyncio.gather(*tasks)
    for r in results:
        print(f"  {r}")


# --- Queue: producer/consumer pattern ---

async def sensor_producer(queue: asyncio.Queue[dict], count: int):
    for i in range(count):
        reading = {
            "sensor_id": f"SEN-{i:03d}",
            "value": round(random.uniform(0, 100), 1),
            "timestamp": f"2347-03-18T{10+i}:00:00Z",
        }
        await queue.put(reading)
        print(f"  [producer] Queued {reading['sensor_id']}")
        await asyncio.sleep(0.1)
    await queue.put(None)  # sentinel


async def sensor_consumer(queue: asyncio.Queue[dict]):
    processed = 0
    while True:
        reading = await queue.get()
        if reading is None:
            break
        label = "ALERT" if reading["value"] > 80 else "OK"
        print(f"  [consumer] {reading['sensor_id']} = {reading['value']} [{label}]")
        processed += 1
        queue.task_done()
    print(f"  [consumer] Processed {processed} readings")


async def demo_queue():
    print("\n--- Queue: producer/consumer ---")
    queue: asyncio.Queue[dict] = asyncio.Queue(maxsize=3)
    await asyncio.gather(sensor_producer(queue, 5), sensor_consumer(queue))


# --- Timeout ---

async def deep_space_scan():
    print("  Starting deep-space scan (takes 5s)...")
    await asyncio.sleep(5)
    return "Signal found!"


async def demo_timeout():
    print("\n--- Timeout ---")
    try:
        result = await asyncio.wait_for(deep_space_scan(), timeout=1.0)
        print(f"  {result}")
    except asyncio.TimeoutError:
        print("  Scan timed out after 1s — aborting.")


# --- Cancellation ---

async def continuous_monitor():
    cycle = 0
    try:
        while True:
            cycle += 1
            print(f"  [monitor] Cycle {cycle} — all clear")
            await asyncio.sleep(0.3)
    except asyncio.CancelledError:
        print(f"  [monitor] Cancelled after {cycle} cycles — cleaning up")
        raise


async def demo_cancellation():
    print("\n--- Cancellation ---")
    task = asyncio.create_task(continuous_monitor())
    await asyncio.sleep(1.0)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        print("  Monitor task cancelled cleanly.")


async def main():
    await demo_basic()
    await demo_concurrent()
    await demo_queue()
    await demo_timeout()
    await demo_cancellation()
    print("\n--- All async demos complete ---\n")


if __name__ == "__main__":
    asyncio.run(main())
