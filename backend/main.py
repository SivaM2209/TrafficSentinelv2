from pathlib import Path
import shutil

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from database.database import create_tables
from api.routes.vehicles import router as vehicles_router
from services.uploaded_video_processor import process_uploaded_video

app = FastAPI(
    title="NexTra API",
    description="NexTra AI-powered traffic intelligence backend",
    version="2.0.0",
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

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_PATH = PROJECT_ROOT / "frontend"
UPLOAD_PATH = PROJECT_ROOT / "data" / "uploads"
PROCESSED_PATH = PROJECT_ROOT / "data" / "processed_videos"
UPLOAD_PATH.mkdir(parents=True, exist_ok=True)
PROCESSED_PATH.mkdir(parents=True, exist_ok=True)


@app.get("/")
def serve_frontend():
    return FileResponse(FRONTEND_PATH / "index.html")


@app.get("/style.css")
def serve_css():
    return FileResponse(FRONTEND_PATH / "style.css", media_type="text/css")


@app.get("/script.js")
def serve_js():
    return FileResponse(FRONTEND_PATH / "script.js", media_type="application/javascript")


@app.get("/logo.svg")
def serve_logo():
    return FileResponse(FRONTEND_PATH / "logo.svg", media_type="image/svg+xml")


@app.get("/api-status")
def api_status():
    return {"message": "NexTra API is running", "status": "online"}


@app.post("/upload-video/{camera_id}")
async def upload_video(camera_id: int, file: UploadFile = File(...)):
    if camera_id not in [1, 2, 3]:
        return {"error": "Invalid camera ID. Use 1, 2, or 3."}
    if not file.filename:
        return {"error": "No file selected."}

    camera_folder = UPLOAD_PATH / f"camera_{camera_id}"
    camera_folder.mkdir(parents=True, exist_ok=True)
    original_path = camera_folder / file.filename

    with original_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "message": "Video uploaded successfully",
        "camera_id": camera_id,
        "filename": file.filename,
    }


@app.post("/analyze-video/{camera_id}")
def analyze_video(camera_id: int):
    if camera_id not in [1, 2, 3]:
        return {"error": "Invalid camera ID. Use 1, 2, or 3."}

    camera_folder = UPLOAD_PATH / f"camera_{camera_id}"
    if not camera_folder.exists():
        return {"error": "No video uploaded for this camera."}

    videos = [p for p in camera_folder.iterdir() if p.is_file()]
    if not videos:
        return {"error": "No uploaded video found for this camera."}

    input_path = max(videos, key=lambda p: p.stat().st_mtime)

    try:
        processed_output, summary = process_uploaded_video(camera_id, input_path)
    except Exception as error:
        return {"error": f"Video processing failed: {str(error)}"}

    return {
        "message": "Video analyzed successfully",
        "camera_id": camera_id,
        "video_url": f"/processed-video/{camera_id}",
        "summary": summary,
    }


@app.get("/processed-video/{camera_id}")
def get_processed_video(camera_id: int):
    if camera_id not in [1, 2, 3]:
        return {"error": "Invalid camera ID."}
    video_path = PROCESSED_PATH / f"camera_{camera_id}" / "processed_video.mp4"
    if not video_path.exists():
        return {"error": "Processed video not found."}
    return FileResponse(video_path, media_type="video/mp4", headers={"Content-Disposition": "inline"})


@app.get("/analysis-summary/{camera_id}")
def get_analysis_summary(camera_id: int):
    if camera_id not in [1, 2, 3]:
        return {"error": "Invalid camera ID."}
    summary_path = PROCESSED_PATH / f"camera_{camera_id}" / "analysis_summary.json"
    if not summary_path.exists():
        return {"error": "No analysis summary found for this camera."}
    import json
    return json.loads(summary_path.read_text(encoding="utf-8"))
