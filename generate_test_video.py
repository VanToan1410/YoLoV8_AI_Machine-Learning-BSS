#!/usr/bin/env python3
"""Generate a test video with fake license plates for testing the system."""

import cv2
import numpy as np
import random
import os

OUTPUT = os.path.join(os.path.dirname(__file__), "Test_video.mp4")
WIDTH, HEIGHT = 1280, 720
FPS = 15
DURATION = 30  # seconds
TOTAL_FRAMES = FPS * DURATION

PLATES = [
    "51F-123.45",
    "30A-567.89",
    "92C-111.22",
    "43B-999.88",
    "29H-456.78",
    "88A-321.65",
    "77C-888.77",
    "50F-246.80",
]


def draw_plate(frame, text, x, y, scale=1.0):
    """Draw a realistic-looking license plate on the frame."""
    pw, ph = int(220 * scale), int(50 * scale)
    # White plate background
    cv2.rectangle(frame, (x, y), (x + pw, y + ph), (255, 255, 255), -1)
    # Border
    cv2.rectangle(frame, (x, y), (x + pw, y + ph), (0, 0, 0), 2)
    # Text
    font_scale = 0.7 * scale
    thickness = max(1, int(2 * scale))
    text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)[0]
    tx = x + (pw - text_size[0]) // 2
    ty = y + (ph + text_size[1]) // 2
    cv2.putText(frame, text, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 0), thickness)


def draw_car(frame, x, y, w, h, color):
    """Draw a simple car rectangle."""
    cv2.rectangle(frame, (x, y), (x + w, y + h), color, -1)
    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 0), 2)
    # Windshield
    cv2.rectangle(frame, (x + 10, y + 5), (x + w - 10, y + int(h * 0.3)), (180, 200, 220), -1)


def main():
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(OUTPUT, fourcc, FPS, (WIDTH, HEIGHT))

    print(f"Generating test video: {OUTPUT}")
    print(f"  Resolution: {WIDTH}x{HEIGHT}")
    print(f"  FPS: {FPS}, Duration: {DURATION}s")

    cars = []
    for i in range(4):
        cars.append({
            "plate": random.choice(PLATES),
            "x": random.randint(-300, WIDTH),
            "y": random.randint(200, 500),
            "speed": random.uniform(1.5, 4.0),
            "color": (random.randint(50, 200), random.randint(50, 200), random.randint(50, 200)),
            "scale": random.uniform(0.8, 1.5),
        })

    for frame_idx in range(TOTAL_FRAMES):
        # Background - road scene
        frame = np.full((HEIGHT, WIDTH, 3), (80, 80, 80), dtype=np.uint8)
        # Sky
        frame[:HEIGHT // 3] = (180, 140, 100)
        # Road
        cv2.rectangle(frame, (0, HEIGHT // 3), (WIDTH, HEIGHT), (60, 60, 60), -1)
        # Lane markings
        for lx in range(0, WIDTH, 100):
            offset = int(frame_idx * 2) % 100
            cv2.rectangle(frame, (lx - offset, HEIGHT // 2 - 2), (lx - offset + 50, HEIGHT // 2 + 2),
                          (200, 200, 200), -1)

        for car in cars:
            cx = int(car["x"])
            cy = int(car["y"])
            cw = int(160 * car["scale"])
            ch = int(90 * car["scale"])

            if 0 < cx < WIDTH and 0 < cy < HEIGHT:
                draw_car(frame, cx, cy, cw, ch, car["color"])
                px = cx + (cw - int(220 * car["scale"])) // 2
                py = cy + ch - int(60 * car["scale"])
                draw_plate(frame, car["plate"], px, py, car["scale"])

            car["x"] += car["speed"]
            if car["x"] > WIDTH + 300:
                car["x"] = random.randint(-400, -100)
                car["y"] = random.randint(250, 550)
                car["plate"] = random.choice(PLATES)
                car["speed"] = random.uniform(1.5, 4.0)
                car["scale"] = random.uniform(0.8, 1.5)
                car["color"] = (random.randint(50, 200), random.randint(50, 200), random.randint(50, 200))

        # Timestamp
        import time
        ts = f"TEST VIDEO - Frame {frame_idx}/{TOTAL_FRAMES}"
        cv2.putText(frame, ts, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

        out.write(frame)

    out.release()
    print(f"Done! Video saved to: {OUTPUT}")


if __name__ == "__main__":
    main()
