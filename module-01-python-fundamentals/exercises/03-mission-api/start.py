"""
Exercise 03 — Mission API
Build a FastAPI CRUD app for mission records.
"""

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException

DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"


def create_app() -> FastAPI:
    """Create and return a configured FastAPI application."""
    app = FastAPI(title="DSS Pathfinder — Mission API")

    @app.on_event("startup")
    async def load_data():
        app.state.missions = json.loads((DATA_DIR / "missions.json").read_text())

    # TODO: implement the following endpoints:
    #
    # GET  /missions           — return {"count": N, "missions": [...]}
    #                            optional query param: status (filter by status)
    #
    # GET  /missions/{mission_id} — return the mission dict, or 404
    #
    # POST /missions           — accept a JSON body, append to missions list,
    #                            return the new mission with status 201
    #
    # PATCH /missions/{mission_id} — accept partial JSON, merge into existing
    #                                mission, return updated mission (or 404)

    return app


app = create_app()
