"""
Exercise 02 — Async Sensor Relay (solution)
"""

import asyncio
from dataclasses import dataclass


@dataclass
class SensorReading:
    sensor_id: str
    value: float
    timestamp: str


async def produce_readings(
    queue: asyncio.Queue,
    readings: list[SensorReading],
) -> None:
    for reading in readings:
        await queue.put(reading)
        await asyncio.sleep(0.01)
    await queue.put(None)


async def consume_readings(
    queue: asyncio.Queue,
    threshold: float = 80.0,
) -> list[tuple[str, str]]:
    results: list[tuple[str, str]] = []
    while True:
        reading = await queue.get()
        if reading is None:
            break
        classification = "ALERT" if reading.value > threshold else "OK"
        results.append((reading.sensor_id, classification))
        queue.task_done()
    return results


async def relay_with_timeout(
    readings: list[SensorReading],
    threshold: float = 80.0,
    timeout: float = 5.0,
) -> list[tuple[str, str]]:
    queue: asyncio.Queue = asyncio.Queue(maxsize=5)

    async def _run() -> list[tuple[str, str]]:
        consumer_task = asyncio.create_task(consume_readings(queue, threshold))
        await produce_readings(queue, readings)
        return await consumer_task

    return await asyncio.wait_for(_run(), timeout=timeout)
