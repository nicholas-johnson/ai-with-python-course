# Exercise 2: Multimodal — Vision and Audio

## Recap

GPT-4o is a multimodal model — it can process images alongside text. OpenAI also provides the Whisper API for audio transcription. Adding these to your Research Assistant gives users the ability to:

- **Drop an image** into the chat and get structured analysis
- **Upload a voice memo** and get a transcript

This is the fun one. Two small functions, two endpoints, and suddenly your assistant can see and hear.

### Vision with GPT-4o

Send images as base64 data URLs in the message content:

```python
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Describe this image."},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{image_b64}"},
                },
            ],
        }
    ],
)
```

### Audio with Whisper

```python
transcript = client.audio.transcriptions.create(
    model="whisper-1",
    file=audio_file,
)
print(transcript.text)
```

## What you build

Two new endpoints added to `start.py` (which ships with the Exercise 1 solution — chat and tools already work):

| Endpoint | Method | Description |
|---|---|---|
| `/vision` | POST | Accepts `{"image": "<base64>", "prompt": "..."}`, returns structured analysis |
| `/transcribe` | POST | Accepts audio file upload, returns `{"transcript": "..."}` |

## Step-by-step

### 1. Implement `transcribe_audio`

Wrap the audio bytes in an `io.BytesIO` with a `.name` attribute, then call the Whisper API:

```python
audio_file = io.BytesIO(audio_bytes)
audio_file.name = "audio.wav"
transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
return transcript.text
```

### 2. Implement `analyze_image`

Build a chat completion with GPT-4o that includes the image as a base64 data URL. Ask the model to respond in JSON with `description` and `key_points` fields. Use `response_format={"type": "json_object"}` to enforce JSON output.

### 3. Add `POST /vision`

```python
@app.post("/vision")
async def vision(req: VisionRequest):
    result = await analyze_image(req.image, req.prompt)
    return VisionResponse(
        description=result.get("description", ""),
        key_points=result.get("key_points", []),
    )
```

### 4. Add `POST /transcribe`

```python
from fastapi import UploadFile, File

@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    audio_bytes = await file.read()
    text = await transcribe_audio(audio_bytes)
    return {"transcript": text}
```

### 5. Test with the frontend

Start the backend and frontend. Try:
- Click the image button and upload a photo — the image analysis panel appears
- Click the microphone button and upload a voice memo — the transcript appears in the chat
- Keep chatting — everything from Exercise 1 still works

## Try it

```bash
# Terminal 1
cd module-04-genai-strategies/exercises/02-multimodal
uvicorn start:app --reload --port 8000

# Terminal 2
cd module-04-genai-strategies/frontend
pnpm dev
```

## Tests

```bash
pytest test_start.py -v
```

The tests check:
- `/vision` accepts a base64 image and returns a description
- `/transcribe` accepts an audio file and returns a transcript
- All previous endpoints still work

## Stretch goals

- Support multiple images in a single `/vision` request
- Pipe the transcript into the chat automatically so the AI can respond to what you said
- Add a `/tts` endpoint that speaks the assistant's response back using OpenAI's TTS API
