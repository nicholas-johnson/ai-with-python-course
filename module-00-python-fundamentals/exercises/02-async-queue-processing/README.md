# Exercise 02 — Async Queue Processing

Build an async producer/consumer pipeline with `asyncio.Queue`, backpressure, sentinel-based shutdown, and timeout handling.

## Objectives

1. Implement `SensorReading` — a dataclass with `sensor_id`, `value` (float), and `timestamp` (str).
2. Implement `produce_readings(queue, readings)` — an async function that puts each reading into the queue, with a small delay between them.
3. Implement `consume_readings(queue, threshold)` — an async consumer that pulls readings, classifies them as `"ALERT"` (value > threshold) or `"OK"`, and returns a list of `(sensor_id, classification)` tuples. Stops when it receives `None`.
4. Implement `relay_with_timeout(readings, threshold, timeout)` — runs producer and consumer concurrently with an overall timeout. Returns the consumer's results, or raises `TimeoutError` if the pipeline exceeds the deadline.

## Run the tests

```bash
pytest module-00-python-fundamentals/exercises/02-async-queue-processing/test_start.py -v
```

## Hints

- Use `asyncio.Queue` with a small `maxsize` to create backpressure.
- The producer should put `None` as a sentinel to signal completion.
- `asyncio.wait_for` wraps a coroutine with a timeout.
