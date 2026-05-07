"""
Exercise 03 — Mission API (solution)
"""

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"


def create_app() -> FastAPI:
    app = FastAPI(title="DSS Pathfinder — Mission API")

    @app.on_event("startup")
    async def load_data():
        app.state.missions = json.loads((DATA_DIR / "missions.json").read_text())

    @app.get("/missions")
    async def list_missions(status: str | None = None):
        results = app.state.missions
        if status:
            results = [m for m in results if m["status"] == status]
        return {"count": len(results), "missions": results}

    @app.get("/missions/{mission_id}")
    async def get_mission(mission_id: str):
        for m in app.state.missions:
            if m["id"] == mission_id:
                return m
        raise HTTPException(status_code=404, detail=f"Mission {mission_id} not found")

    @app.post("/missions", status_code=201)
    async def create_mission(request: Request):
        body = await request.json()
        app.state.missions.append(body)
        return body

    @app.patch("/missions/{mission_id}")
    async def update_mission(mission_id: str, request: Request):
        body = await request.json()
        for m in app.state.missions:
            if m["id"] == mission_id:
                m.update(body)
                return m
        raise HTTPException(status_code=404, detail=f"Mission {mission_id} not found")

    return app


app = create_app()
