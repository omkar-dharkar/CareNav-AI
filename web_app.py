"""Custom web interface for CareNav AI."""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from pydantic import BaseModel, Field

from carenav_agents.agent import root_agent
from carenav_agents.config import config
from carenav_agents.hospital_finder_agent import find_nearby_hospitals

load_dotenv()

APP_NAME = "carenav_web"
USER_ID = "carenav_ui_user"
BASE_DIR = Path(__file__).resolve().parent
UI_DIR = BASE_DIR / "ui"

session_service = InMemorySessionService()
runner = Runner(
    app_name=APP_NAME,
    agent=root_agent,
    session_service=session_service,
)

app = FastAPI(
    title="CareNav AI",
    description="A U.S.-focused healthcare navigation interface.",
    version="1.0.0",
)
app.mount("/static", StaticFiles(directory=UI_DIR), name="static")


class SessionResponse(BaseModel):
    session_id: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    session_id: str | None = None


class ChatResponse(BaseModel):
    session_id: str
    text: str
    model: str
    tools: list[str] = Field(default_factory=list)


class HospitalsRequest(BaseModel):
    radius: int = Field(default=5000, ge=1000, le=50000)
    care_type: str = Field(default="emergency")
    insurance_provider: str = Field(default="", max_length=120)


class HospitalsResponse(BaseModel):
    text: str


async def _ensure_session(session_id: str | None) -> str:
    if session_id:
        existing = await session_service.get_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=session_id,
        )
        if existing:
            return session_id

    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=session_id or str(uuid.uuid4()),
    )
    return session.id


def _event_text(event: Any) -> str:
    content = getattr(event, "content", None)
    if not content or getattr(content, "role", "") != "model":
        return ""

    text_parts: list[str] = []
    for part in getattr(content, "parts", None) or []:
        text = getattr(part, "text", None)
        if text:
            text_parts.append(text)

    return "\n".join(text_parts).strip()


def _event_tools(event: Any) -> list[str]:
    content = getattr(event, "content", None)
    if not content:
        return []

    tools: list[str] = []
    for part in getattr(content, "parts", None) or []:
        function_call = getattr(part, "function_call", None)
        if function_call and getattr(function_call, "name", None):
            tools.append(function_call.name)
    return tools


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(UI_DIR / "index.html")


@app.get("/api/health")
async def health() -> dict[str, Any]:
    return {
        "ok": True,
        "project": config.PROJECT_NAME,
        "author": config.AUTHOR,
        "model": config.DEFAULT_MODEL,
        "emergency": config.EMERGENCY_NUMBER,
        "places_configured": bool(os.getenv("GOOGLE_PLACES_API_KEY")),
    }


@app.post("/api/session")
async def create_session() -> SessionResponse:
    session_id = await _ensure_session(None)
    return SessionResponse(session_id=session_id)


@app.post("/api/chat")
async def chat(request: ChatRequest) -> ChatResponse:
    session_id = await _ensure_session(request.session_id)
    message = types.Content(
        role="user",
        parts=[types.Part(text=request.message.strip())],
    )

    response_parts: list[str] = []
    tools: list[str] = []

    try:
        async for event in runner.run_async(
            user_id=USER_ID,
            session_id=session_id,
            new_message=message,
        ):
            text = _event_text(event)
            if text:
                response_parts.append(text)
            for tool in _event_tools(event):
                if tool not in tools:
                    tools.append(tool)
    except Exception as exc:
        detail = str(exc)
        if "RESOURCE_EXHAUSTED" in detail or "429" in detail:
            detail = (
                "Gemini quota is currently exhausted for this project. "
                "Nearby-care search can still run from the Finder panel."
            )
        raise HTTPException(status_code=502, detail=detail) from exc

    text = "\n\n".join(response_parts).strip()
    if not text:
        text = "I could not produce a response. Please try again in a moment."

    return ChatResponse(
        session_id=session_id,
        text=text,
        model=config.DEFAULT_MODEL,
        tools=tools,
    )


@app.post("/api/hospitals")
async def hospitals(request: HospitalsRequest) -> HospitalsResponse:
    text = find_nearby_hospitals(
        radius=request.radius,
        care_type=request.care_type,
        insurance_provider=request.insurance_provider,
    )
    return HospitalsResponse(text=text)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "web_app:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", os.getenv("CARENAV_UI_PORT", "8080"))),
        reload=False,
    )
