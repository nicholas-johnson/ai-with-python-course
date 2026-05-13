# Exercise 3: Multimodal -- Vision and Audio

## Recap

GPT-4o is a multimodal model -- it can process images alongside text. OpenAI also provides the Whisper API for audio transcription. Adding these to your Research Assistant gives users the ability to:

- **Drop an image** into the chat and get structured analysis
- **Upload a voice memo** and get a transcript

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

Two new endpoints added to `start.py`:

| Endpoint | Method | Description |
|---|---|---|
| `/vision` | POST | Accepts `{"image": "<base64>", "prompt": "..."}`, returns structured analysis |
| `/transcribe` | POST | Accepts audio file upload, returns `{"transcript": "..."}` |

## Step-by-step

### 1. Start from the Exercise 2 solution

Your `start.py` ships with the working chat + tools from Exercise 2. The MCP server is provided.

### 2. Add `POST /vision`

Create an endpoint that:

1. Accepts a JSON body with `image` (base64 string) and `prompt` (optional string)
2. Sends the image to GPT-4o using the multimodal message format
3. Returns a structured JSON response with `description` and `key_points`

```python
class VisionRequest(BaseModel):
    image: str
    prompt: str = "Describe and analyse this image in detail."

class VisionResponse(BaseModel):
    description: str
    key_points: list[str]

@app.post("/vision")
async def vision(req: VisionRequest):
    # TODO: send image to GPT-4o, parse response into VisionResponse
    pass
```

**Hint:** Ask the model to respond in JSON format and parse it, or use the content directly and extract key points.

### 3. Add `POST /transcribe`

Create an endpoint that:

1. Accepts a file upload using `fastapi.UploadFile`
2. Sends the audio to OpenAI's Whisper API
3. Returns the transcript

```python
from fastapi import UploadFile, File

@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    # TODO: read file, send to Whisper, return transcript
    pass
```

**Hint:** Whisper expects a file-like object. You can use `io.BytesIO`:

```python
import io
audio_bytes = await file.read()
audio_file = io.BytesIO(audio_bytes)
audio_file.name = file.filename
```

### 4. Test with the frontend

Start the backend and frontend. Try:
- Uploading a screenshot or photo -- the image analysis panel appears
- Uploading a voice memo -- the transcript appears in the chat

## Try it

```bash
# Terminal 1
cd module-04-genai-strategies/exercises/03-multimodal
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
- Add a `/vision` option to choose between quick description and detailed analysis
- Pipe the transcript into the chat automatically so the AI can respond to it
