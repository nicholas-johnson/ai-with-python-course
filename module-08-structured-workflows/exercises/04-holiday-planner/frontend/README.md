# Holiday Planner Frontend

SvelteKit + Tailwind + ShadCN frontend for the Holiday Planner agent.

## Quick Start

```bash
cd frontend
pnpm install
pnpm dev
```

The dev server starts at `http://localhost:5173` and proxies `/api` requests to `http://localhost:8000`.

## Backend Endpoints

| Endpoint | Method | Description |
| --- | --- | --- |
| `/chat` | POST (SSE) | Streaming chat with the holiday planner agent |
| `/plan` | POST | Generate a structured plan (returns JSON array of steps) |
| `/preferences` | GET | Retrieve remembered user preferences |
| `/health` | GET | Health check |

Start the backend before running the frontend:

```bash
cd .. && python server.py
```
