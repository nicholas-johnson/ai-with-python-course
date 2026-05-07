"""Tests for Exercise 02 — Async Sensor Relay."""

import asyncio

import pytest

from start import SensorReading, consume_readings, produce_readings, relay_with_timeout


def make_readings(count: int = 5, high_value_index: int = 2) -> list[SensorReading]:
    readings = []
    for i in range(count):
        value = 95.0 if i == high_value_index else 50.0
        readings.append(SensorReading(
            sensor_id=f"SEN-{i:03d}",
            value=value,
            timestamp=f"2347-03-18T{10 + i}:00:00Z",
        ))
    return readings


class TestSensorReading:
    def test_fields(self):
        r = SensorReading(sensor_id="SEN-001", value=42.5, timestamp="2347-03-18T10:00:00Z")
        assert r.sensor_id == "SEN-001"
        assert r.value == 42.5
        assert r.timestamp == "2347-03-18T10:00:00Z"


class TestProduceReadings:
    @pytest.mark.asyncio
    async def test_puts_all_readings_then_sentinel(self):
        queue: asyncio.Queue = asyncio.Queue()
        readings = make_readings(3)
        await produce_readings(queue, readings)

        items = []
        while not queue.empty():
            items.append(await queue.get())

        assert len(items) == 4  # 3 readings + None sentinel
        assert items[-1] is None
        assert all(isinstance(r, SensorReading) for r in items[:-1])


class TestConsumeReadings:
    @pytest.mark.asyncio
    async def test_classifies_readings(self):
        queue: asyncio.Queue = asyncio.Queue()
        await queue.put(SensorReading("SEN-001", 50.0, "t1"))
        await queue.put(SensorReading("SEN-002", 95.0, "t2"))
        await queue.put(SensorReading("SEN-003", 80.0, "t3"))
        await queue.put(None)

        results = await consume_readings(queue, threshold=80.0)

        assert results == [
            ("SEN-001", "OK"),
            ("SEN-002", "ALERT"),
            ("SEN-003", "OK"),
        ]

    @pytest.mark.asyncio
    async def test_custom_threshold(self):
        queue: asyncio.Queue = asyncio.Queue()
        await queue.put(SensorReading("SEN-001", 50.0, "t1"))
        await queue.put(None)

        results = await consume_readings(queue, threshold=40.0)
        assert results == [("SEN-001", "ALERT")]


class TestRelayWithTimeout:
    @pytest.mark.asyncio
    async def test_processes_all_readings(self):
        readings = make_readings(5, high_value_index=2)
        results = await relay_with_timeout(readings, threshold=80.0, timeout=5.0)

        assert len(results) == 5
        sensor_ids = [r[0] for r in results]
        assert sensor_ids == [f"SEN-{i:03d}" for i in range(5)]

    @pytest.mark.asyncio
    async def test_alert_classification(self):
        readings = make_readings(3, high_value_index=1)
        results = await relay_with_timeout(readings, threshold=80.0, timeout=5.0)

        classifications = {r[0]: r[1] for r in results}
        assert classifications["SEN-001"] == "ALERT"
        assert classifications["SEN-000"] == "OK"

    @pytest.mark.asyncio
    async def test_empty_readings(self):
        results = await relay_with_timeout([], threshold=80.0, timeout=5.0)
        assert results == []
