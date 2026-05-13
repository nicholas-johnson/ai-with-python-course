# Exercise 02 — Vision

**Goal:** Send images to GPT-4o and get structured analysis back. Builds on Exercise 01's `MissionReport` model.

## What you build

1. `encode_image(path)` — read an image file and return a base64-encoded string.
2. `analyse_image(client, image_source, prompt)` — build a multimodal message (text + image), call GPT-4o, and return a validated `MissionReport`.
3. A CLI: `python start.py path/to/image.png` analyses the image and prints a structured report.

## Run it

```bash
python start.py path/to/image.png
# or pass a URL:
python start.py https://example.com/photo.jpg
```

## Run the tests

```bash
pytest module-04-genai-strategies/exercises/02-vision/test_start.py -v
```
