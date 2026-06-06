#!/usr/bin/env python3
"""
VAN TOAN - Vehicle Management System

Usage:
    python main.py                              # Webcam + API server
    python main.py --source video.mp4           # Video file
    python main.py --source rtsp://...          # RTSP camera
    python main.py --api-only                   # API server only
    python main.py --headless --source video.mp4 # No GUI window
"""

import argparse
import logging
import threading
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("bss")


def main():
    parser = argparse.ArgumentParser(description="BSS - Vehicle Management System")
    parser.add_argument("--source", type=str, default=None,
                        help="Video source: file path, RTSP URL, or camera index (default: 0)")
    parser.add_argument("--camera-id", type=int, default=1,
                        help="Camera ID in database (default: 1)")
    parser.add_argument("--api-only", action="store_true",
                        help="Run API server only")
    parser.add_argument("--headless", action="store_true",
                        help="No OpenCV window")
    parser.add_argument("--host", type=str, default="0.0.0.0",
                        help="API host (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=6789,
                        help="API port (default: 6789)")
    args = parser.parse_args()

    log.info("BSS Vehicle Management System v2.0 starting")

    from backend.database import init_db
    import uvicorn

    if args.api_only:
        log.info("Mode: API only")
        log.info("API server: http://%s:%d", args.host, args.port)
        uvicorn.run("backend.app:app", host=args.host, port=args.port, log_level="info")
    else:
        from backend.services.processor import run_processor

        source = args.source or "0"
        log.info("Video source: %s", source)
        log.info("Camera ID: %d", args.camera_id)
        log.info("Headless: %s", args.headless)
        log.info("API server: http://%s:%d", args.host, args.port)

        api_thread = threading.Thread(
            target=lambda: uvicorn.run(
                "backend.app:app",
                host=args.host,
                port=args.port,
                log_level="warning",
            ),
            daemon=True,
        )
        api_thread.start()
        log.info("API server started")

        run_processor(
            source=int(source) if source.isdigit() else source,
            camera_id=args.camera_id,
            headless=args.headless,
            max_fps=15,
        )


if __name__ == "__main__":
    main()
