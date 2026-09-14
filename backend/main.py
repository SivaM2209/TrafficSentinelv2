from pathlib import Path
import shutil
import subprocess

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from database.database import create_tables
from api.routes.vehicles import router as vehicles_router
from services.uploaded_video_processor import process_uploaded_video


app = FastAPI(
    title="TrafficSentinel API",
    description="Backend API for TrafficSentinel",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

create_tables()
app.include_router(vehicles_router)


# =========================
# PROJECT PATHS
# =========================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

FRONTEND_PATH = PROJECT_ROOT / "frontend"

VIDEO_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed_videos"
    / "traffic_detected_web.mp4"
)
UPLOAD_PATH = PROJECT_ROOT / "data" / "uploads"

UPLOAD_PATH.mkdir(
    parents=True,
    exist_ok=True
)


# =========================
# FRONTEND
# =========================

@app.get("/")
def serve_frontend():
    return FileResponse(
        FRONTEND_PATH / "index.html"
    )


@app.get("/style.css")
def serve_css():
    return FileResponse(
        FRONTEND_PATH / "style.css",
        media_type="text/css"
    )


@app.get("/script.js")
def serve_js():
    return FileResponse(
        FRONTEND_PATH / "script.js",
        media_type="application/javascript"
    )


# =========================
# API
# =========================

@app.get("/api-status")
def api_status():
    return {
        "message": "TrafficSentinel API is running"
    }


# =========================
# PROCESSED VIDEO
# =========================

@app.get("/video")
def get_processed_video():

    if not VIDEO_PATH.exists():
        return {
            "error": "Processed video not found",
            "path": str(VIDEO_PATH)
        }

    return FileResponse(
        path=VIDEO_PATH,
        media_type="video/mp4",
        headers={
            "Content-Disposition": "inline"
        }
    )
# =========================
# VIDEO UPLOAD
# =========================

@app.post("/upload-video/{camera_id}")
async def upload_video(
    camera_id: int,
    file: UploadFile = File(...)
):

    if camera_id not in [1, 2, 3]:
        return {
            "error": "Invalid camera ID. Use 1, 2, or 3."
        }

    if not file.filename:
        return {
            "error": "No file selected."
        }

    camera_folder = UPLOAD_PATH / f"camera_{camera_id}"

    camera_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    # Original uploaded video
    original_path = camera_folder / file.filename

    with original_path.open("wb") as buffer:
        shutil.copyfileobj(
            file.file,
            buffer
        )

    try:

        print()
        print(
            f"Starting processing for Camera {camera_id}..."
        )

        processed_video = process_uploaded_video(
            camera_id,
            original_path
        )

        print(
            f"Camera {camera_id} processing completed."
        )

    except Exception as error:

        print(
            "Video processing failed:",
            error
        )

        return {
            "error": f"Video processing failed: {str(error)}"
        }

    return {
        "message": "Video uploaded and processed successfully",
        "camera_id": camera_id,
        "filename": file.filename,
        "video_url": f"/processed-video/{camera_id}"
    }
# =========================
# UPLOADED VIDEO
# =========================

@app.get("/uploaded-video/{camera_id}")
def get_uploaded_video(camera_id: int):

    camera_folder = UPLOAD_PATH / f"camera_{camera_id}"

    video_path = camera_folder / "video_web.mp4"

    if not video_path.exists():
        return {
            "error": "No converted video found for this camera."
        }

    return FileResponse(
        path=video_path,
        media_type="video/mp4",
        headers={
            "Content-Disposition": "inline"
        }
    )
# =========================
# PROCESSED UPLOADED VIDEO
# =========================

@app.get("/processed-video/{camera_id}")
def get_processed_uploaded_video(camera_id: int):

    if camera_id not in [1, 2, 3]:
        return {
            "error": "Invalid camera ID."
        }

    video_path = (
        PROJECT_ROOT
        / "data"
        / "processed_videos"
        / f"camera_{camera_id}"
        / "processed_video.mp4"
    )

    if not video_path.exists():
        return {
            "error": "Processed video not found."
        }

    return FileResponse(
        path=video_path,
        media_type="video/mp4",
        headers={
            "Content-Disposition": "inline"
        }
    )