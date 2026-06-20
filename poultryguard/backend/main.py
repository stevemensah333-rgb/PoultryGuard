"""
main.py

FastAPI app exposing PoultryGuard's orchestrator pipeline over HTTP, so the
Gradio frontend (or any other client) can call it without importing
backend internals directly. This separation also means the same backend
could later serve a mobile app or WhatsApp bot without changes.

Run with:
    uvicorn backend.main:app --reload --port 8000
"""

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from backend.agents.orchestrator import PoultryGuardOrchestrator
from backend.security import InvalidImageError, validate_and_load_image

app = FastAPI(title="PoultryGuard API", version="0.1.0")

# CORS is open here for local demo convenience. Lock this down to specific
# origins before any real deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

_orchestrator: PoultryGuardOrchestrator | None = None


def get_orchestrator() -> PoultryGuardOrchestrator:
    # Lazy-loaded singleton so the (somewhat slow) CLIP model load only
    # happens once, and only when the first request actually needs it.
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = PoultryGuardOrchestrator()
    return _orchestrator


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/diagnose")
async def diagnose(
    image: UploadFile = File(...),
    lat: float = Form(6.6885),
    lon: float = Form(-1.6244),
    flock_feed_kg: float = Form(10.0),
    include_twi: bool = Form(False),
) -> dict:
    raw_bytes = await image.read()

    try:
        pil_image = validate_and_load_image(raw_bytes)
    except InvalidImageError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    orchestrator = get_orchestrator()
    report = orchestrator.run(
        image=pil_image,
        farmer_lat=lat,
        farmer_lon=lon,
        flock_feed_kg=flock_feed_kg,
        include_twi=include_twi,
    )
    return report.to_dict()
