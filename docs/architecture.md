# TrafficSentinel — Project Architecture

This document explains what each folder is for and why the project is
laid out this way. Nothing here is implemented yet — this is the
scaffold only.

## Design principle

The project follows a **layered, modular** structure so each concern
(video capture, detection, OCR, storage, API, frontend) lives in its
own place and can be built, tested, and swapped independently.

```
Video Stream → Detection (YOLO) → Tracking → OCR (plates) → Analytics
                                                                 ↓
                                                         SQLite Database
                                                                 ↓
                                                         FastAPI Routes
                                                                 ↓
                                                    HTML/CSS/JS Dashboard
```

## Folder-by-folder

### `app/` — the FastAPI application package
Everything that runs as part of the backend lives here.

- **`app/main.py`** — FastAPI entry point. Creates the app, mounts
  static files/templates, includes routers, handles startup/shutdown
  (e.g. opening the DB, initializing the video stream).

- **`app/core/`** — cross-cutting concerns used everywhere else:
  - `config.py` — app settings (paths, thresholds, camera source),
    loaded from `.env` / `configs/app_config.yaml`.
  - `logging_config.py` — one shared logging setup for the whole app.

- **`app/detection/`** — the computer-vision pipeline (OpenCV + YOLO):
  - `video_stream.py` — reads frames from a file/RTSP/webcam source.
  - `yolo_detector.py` — loads YOLO weights, runs inference, returns
    detections.
  - `vehicle_tracker.py` — keeps consistent IDs for vehicles across
    frames.
  - `traffic_analyzer.py` — turns detections/tracks into traffic
    insights (counts, congestion, violations).

- **`app/ocr/`** — license-plate recognition, kept separate from
  general detection since it's a distinct sub-pipeline:
  - `plate_detector.py` — locates the plate region in a vehicle crop.
  - `plate_reader.py` — runs OCR on the cropped plate.
  - `plate_utils.py` — shared preprocessing/validation helpers.

- **`app/db/`** — persistence layer (SQLite via SQLAlchemy):
  - `database.py` — engine/session setup.
  - `models.py` — ORM table definitions.
  - `crud.py` — reusable create/read/update/delete functions.

- **`app/schemas/`** — Pydantic models that define API request/response
  shapes, kept separate from the DB models so the API contract can
  evolve independently of the schema on disk.

- **`app/services/`** — orchestration/business-logic layer that ties
  detection + ocr + db together, so routes stay thin:
  - `detection_service.py`, `ocr_service.py`, `analytics_service.py`.

- **`app/api/routes/`** — the actual FastAPI endpoints, grouped by
  resource: `vehicles.py`, `plates.py`, `analytics.py`, `stream.py`
  (live updates / WebSocket).

- **`app/utils/`** — small shared helpers (`image_utils.py`,
  `time_utils.py`) used across multiple modules, to avoid duplication.

- **`app/templates/`** and **`app/static/`** — the dashboard frontend
  (HTML/CSS/JS), served directly by FastAPI. `static/css` and
  `static/js` are split for clarity as the dashboard grows.

### `data/` — runtime data, not code
- `raw_videos/` — input video files for testing/demoing.
- `captured_frames/` — frames saved for debugging/inspection.
- `plates/` — cropped plate images saved for OCR debugging.
Kept out of the `app/` package because it's data, not logic, and is
git-ignored (except `.gitkeep`) so the repo doesn't bloat with media.

### `models/` — trained model weights, not code
- `yolo_weights/` — Ultralytics YOLO `.pt` files.
- `ocr_weights/` — OCR model files, if the chosen OCR engine needs any.
Also git-ignored — weights are usually large and are downloaded via
`scripts/download_models.py` rather than committed.

### `tests/` — automated tests (pytest), mirroring `app/`'s structure
as it grows, so each module gets its own test file.

### `scripts/` — one-off/utility scripts that aren't part of the
running application: `download_models.py`, `run_dev_server.sh`.

### `configs/` — non-secret configuration files, e.g.
`app_config.yaml` (camera sources, thresholds). Secrets go in `.env`
instead (see `.env.example`), which is git-ignored.

### `logs/` — rotating log files written by `logging_config.py` at
runtime. Git-ignored except `.gitkeep`.

### `docs/` — project documentation, including this file.

## Why this split?

- **Detection vs. OCR vs. DB are separate packages** so each can be
  developed and unit-tested in isolation — you can test the YOLO
  pipeline on a sample video without touching the database at all.
- **`services/` sits between `api/` and the rest** so route handlers
  never contain business logic directly — this keeps the API layer
  thin and makes it easy to reuse the same logic outside the API
  later (e.g. a CLI or batch script).
- **`schemas/` vs `db/models.py`** are deliberately separate: the
  database shape and the API's public contract are allowed to differ
  and evolve independently.
- **Data and model weights are outside `app/`** since they're not
  source code and shouldn't be committed to version control the same
  way.
