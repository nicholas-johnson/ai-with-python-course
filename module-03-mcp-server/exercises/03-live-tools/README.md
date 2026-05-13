# Exercise 03 -- Live Tools

> Build an MCP server with tools that reach beyond local data -- fetch web pages and manage notes on disk. This is the "it actually does stuff" moment.

## Recap

So far your MCP servers have returned data that was already loaded into memory -- hardcoded dicts or JSON files. This exercise crosses the boundary into **real-world side effects**: fetching live web pages and writing files to disk.

**HTTP tools** let the agent browse the web. The `httpx` library makes this straightforward:

```python
import httpx
import re

def fetch_url(url: str) -> str:
    resp = httpx.get(url, timeout=10, follow_redirects=True)
    resp.raise_for_status()
    text = re.sub(r"<[^>]+>", "", resp.text)  # strip HTML tags
    return text[:5000]  # truncate to fit context
```

Three important details: set a **timeout** so the agent does not hang on slow servers, **strip HTML** to give the model clean text rather than markup, and **truncate** to avoid blowing up the context window.

**File I/O tools** let the agent save and retrieve information. The key safety consideration is **path sanitisation** -- never let a user-controlled filename escape the intended directory:

```python
def save_note(filename: str, content: str) -> str:
    if ".." in filename or "/" in filename:
        return json.dumps({"error": "Invalid filename"})
    (NOTES_DIR / filename).write_text(content)
    return json.dumps({"saved": filename, "bytes": len(content)})
```

Rejecting filenames containing `..` or `/` prevents path traversal attacks. In production you would also canonicalise the path and check it is still inside the target directory.

This exercise builds on Exercise 01. The agent code in `start.py` is provided from the Exercise 01 solution -- it connects to your server and runs the chat loop. You only need to implement `server.py`.

This exercise uses `httpx` (for HTTP requests) and `mcp` -- both are installed via the project's `pyproject.toml`.

## What you build

**`server.py`** -- a FastMCP server with 4 tools:
- `fetch_url(url)` -- fetch a web page, strip HTML, return text
- `save_note(filename, content)` -- save text to a `notes/` directory
- `list_notes()` -- list all saved notes
- `read_note(filename)` -- read a saved note back

**`start.py`** is provided (agent code from Exercise 01).

## Step-by-step

### 1. `fetch_url(url: str) -> str`

Fetch a web page and return cleaned text:

1. Call `httpx.get(url, timeout=10, follow_redirects=True)`.
2. Call `resp.raise_for_status()` to catch HTTP errors.
3. Strip HTML tags: `re.sub(r"<[^>]+>", "", resp.text)`.
4. Optionally collapse whitespace: `re.sub(r"\s+", " ", text).strip()`.
5. Truncate to 5000 characters to avoid overflowing the context.
6. Wrap everything in a `try/except` -- on any error, return `json.dumps({"error": str(e)})`.

You will need to add `import httpx` and `import re` at the top of `server.py`.

The tests check that a bad URL returns an error JSON (not a crash), and that the return type is always a string.

### 2. `save_note(filename: str, content: str) -> str`

Save text to the `notes/` directory:

1. **Sanitise the filename**: if it contains `".."` or `"/"`, return `json.dumps({"error": "Invalid filename"})`.
2. Write the content: `(NOTES_DIR / filename).write_text(content)`.
3. Return `json.dumps({"saved": filename, "bytes": len(content)})`.

The `NOTES_DIR` constant and `mkdir` call are already in the starter code.

The tests check that the file is created with the right content, and that path traversal attempts are rejected.

### 3. `list_notes() -> str`

List all files in `NOTES_DIR`:

1. Iterate over `NOTES_DIR.iterdir()`, filter to files (`.is_file()`).
2. Collect the filenames (`.name`).
3. Return `json.dumps(sorted(filenames))`.

The tests check the empty case and the case after saving some notes.

### 4. `read_note(filename: str) -> str`

Read a saved note:

1. **Sanitise the filename**: reject `".."` or `"/"` as above.
2. Build the path: `NOTES_DIR / filename`.
3. If the file does not exist, return `json.dumps({"error": f"Note not found: {filename}"})`.
4. Otherwise, return `path.read_text()`.

The tests check reading an existing note, reading a missing note, and path traversal rejection.

## Try it

```bash
python start.py
```

On startup, the agent discovers all 4 tools. Try this workflow:

1. `"Fetch the Wikipedia page for the Andromeda Galaxy and give me a 2-sentence summary"` -- the agent calls `fetch_url`, reads the page, and summarises.
2. `"Save a note called andromeda.txt with that summary"` -- the agent calls `save_note`.
3. `"List my notes"` -- the agent calls `list_notes` and shows `andromeda.txt`.
4. `"Read back the andromeda note"` -- the agent calls `read_note` and returns the content.
5. `"Fetch https://httpbin.org/json and save the result as test.json"` -- combines fetch and save in one turn.

## Tests

```bash
pytest module-03-mcp-server/exercises/03-live-tools/test_start.py -v
```

The tests check the server tools directly via FastMCP internals. They use a clean `notes/` directory for each test run. The `fetch_url` test uses a bad URL (localhost) to verify error handling without needing internet access.

## Stretch goals

1. Add a `delete_note(filename)` tool that removes a saved note (with the same path sanitisation).
2. Add a `search_notes(keyword)` tool that searches across all saved notes for a keyword and returns matching filenames with excerpts.
