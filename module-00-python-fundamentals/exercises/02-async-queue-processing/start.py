"""
Exercise 02 — Async Sensor Relay
Build an async producer/consumer pipeline with timeouts.
"""

import asyncio
from dataclasses import dataclass


@dataclass
class SensorReading:
    """A single sensor reading from the Pathfinder's array."""

    # TODO: sensor_id (str), value (float), timestamp (str)
    pass


async def produce_readings(
    queue: asyncio.Queue,
    readings: list[SensorReading],
) -> None:
    """Put each reading into the queue, then send None as a sentinel."""
    # TODO: iterate readings, put each into the queue with a small delay,
    #       then put None to signal completion
    pass


async def consume_readings(
    queue: asyncio.Queue,
    threshold: float = 80.0,
) -> list[tuple[str, str]]:
    """
    Pull readings from the queue until None is received.
    Classify each as "ALERT" (value > threshold) or "OK".
    Return list of (sensor_id, classification) tuples.
    """
    # TODO: consume from queue, classify, collect results
    pass


async def relay_with_timeout(
    readings: list[SensorReading],
    threshold: float = 80.0,
    timeout: float = 5.0,
) -> list[tuple[str, str]]:
    """
    Run the producer/consumer relay with an overall timeout.
    Returns consumer results, or raises TimeoutError.
    """
    # TODO: create queue, run producer + consumer concurrently, apply timeout
    pass


def main() -> None:
    """Run the sensor relay on a small sample batch and print classifications."""
    readings = [
        SensorReading("SEN-000", 50.0, "2347-03-18T10:00:00Z"),
        SensorReading("SEN-001", 95.0, "2347-03-18T11:00:00Z"),
        SensorReading("SEN-002", 72.0, "2347-03-18T12:00:00Z"),
        SensorReading("SEN-003", 88.0, "2347-03-18T13:00:00Z"),
    ]
    results = asyncio.run(relay_with_timeout(readings, threshold=80.0))
    for sensor_id, classification in results:
        print(f"{sensor_id}: {classification}")


if __name__ == "__main__":
    main()
