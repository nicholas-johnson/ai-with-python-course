"""
Demo: HTTP basics — FastAPI server + httpx client.
Run:  python module-00-python-fundamentals/demo/05_http_basics.py

Starts a FastAPI server on port 8001, hits it with httpx, then shuts down.
"""

import asyncio
import json
from pathlib import Path

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

app = FastAPI(title="DSS Pathfinder — Mission Briefing API")

MISSIONS: list[dict] = []


@app.on_event("startup")
async def load_data():
    global MISSIONS
    MISSIONS = json.loads((DATA_DIR / "missions.json").read_text())


@app.get("/health")
async def health():
    return {"status": "operational", "ship": "DSS Pathfinder"}


@app.get("/missions")
async def list_missions(status: str | None = None):
    results = MISSIONS
    if status:
        results = [m for m in results if m["status"] == status]
    return {"count": len(results), "missions": results}


@app.get("/missions/{mission_id}")
async def get_mission(mission_id: str):
    for m in MISSIONS:
        if m["id"] == mission_id:
            return m
    raise HTTPException(status_code=404, detail=f"Mission {mission_id} not found")


async def run_client():
    """Hit the API with httpx to demonstrate the client side."""
    await asyncio.sleep(0.5)  # let server start

    async with httpx.AsyncClient(base_url="http://127.0.0.1:8001") as client:
        print("\n--- httpx client demo ---\n")

        r = await client.get("/health")
        print(f"GET /health → {r.status_code}: {r.json()}")

        r = await client.get("/missions", params={"status": "active"})
        data = r.json()
        print(f"GET /missions?status=active → {data['count']} missions")
        for m in data["missions"]:
            print(f"  {m['id']}  {m['name']}")

        r = await client.get("/missions/MSN-001")
        print(f"GET /missions/MSN-001 → {r.json()['name']}")

        r = await client.get("/missions/MSN-999")
        print(f"GET /missions/MSN-999 → {r.status_code}: {r.json()['detail']}")

    print("\n--- Client demo complete. Press Ctrl+C to stop the server. ---\n")


async def main():
    config = uvicorn.Config(app, host="127.0.0.1", port=8001, log_level="warning")
    server = uvicorn.Server(config)

    client_task = asyncio.create_task(run_client())
    server_task = asyncio.create_task(server.serve())

    await client_task
    server.should_exit = True
    await server_task


if __name__ == "__main__":
    asyncio.run(main())
