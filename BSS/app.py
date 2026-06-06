import os
import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from backend.routes import dashboard, vehicles, records, cameras, watchlist, parking, settings, detect
from backend.services.processor import (
    get_latest_frame_bytes, register_ws_callback, unregister_ws_callback,
    is_running, current_fps, processor_status
)

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

app = FastAPI(
    title="MVA - Vehicle Management System",
    version="2.0.0",
    description="Professional License Plate Recognition & Vehicle Management System"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(dashboard.router)
app.include_router(vehicles.router)
app.include_router(records.router)
app.include_router(cameras.router)
app.include_router(watchlist.router)
app.include_router(parking.router)
app.include_router(settings.router)
app.include_router(detect.router)

# Static files
frontend_dir = os.path.join(BASE_DIR, "frontend")
if os.path.isdir(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")


@app.get("/", response_class=HTMLResponse)
async def index():
    index_path = os.path.join(frontend_dir, "index.html")
    with open(index_path) as f:
        return f.read()


@app.get("/api/stream")
async def video_stream():
    """MJPEG live video stream."""
    import time

    def generate():
        while True:
            frame_bytes = get_latest_frame_bytes()
            if frame_bytes:
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n"
                    + frame_bytes + b"\r\n"
                )
            else:
                time.sleep(0.1)

    return StreamingResponse(
        generate(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


@app.get("/api/system/status")
async def system_status():
    return {
        "processor": processor_status,
        "is_running": is_running,
        "fps": round(current_fps, 1),
    }


# WebSocket for realtime updates
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for ws in self.active_connections[:]:
            try:
                await ws.send_json(message)
            except Exception:
                self.disconnect(ws)


manager = ConnectionManager()
_loop = None


def _on_detection(data):
    """Called from processor thread when plate detected."""
    global _loop
    if _loop and manager.active_connections:
        asyncio.run_coroutine_threadsafe(manager.broadcast(data), _loop)


register_ws_callback(_on_detection)


@app.on_event("startup")
async def startup():
    global _loop
    _loop = asyncio.get_event_loop()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Client can send commands if needed
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
