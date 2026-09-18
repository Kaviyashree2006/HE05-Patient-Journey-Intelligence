import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

# Load .env if present
load_dotenv()

from app.database.connection import init_db
from app.api import (
    patients_router,
    documents_router,
    timeline_router,
    intelligence_router,
    qa_router
)
from app.demo_data.synthetic_dataset import generate_synthetic_documents

FRONTEND_DIST = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))
UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uploads"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables
    init_db()
    # Pre-generate synthetic demo PDF documents
    try:
        generate_synthetic_documents()
    except Exception as e:
        print(f"Notice: Demo PDF generation encountered: {e}")
    yield


app = FastAPI(
    title="Evidence-Linked Patient Journey — HE-05 Medical Document Intelligence",
    description="Transforms heterogeneous medical documents into a structured, chronological, evidence-linked patient timeline.",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Processing Error",
            "detail": str(exc),
            "path": request.url.path
        }
    )

# Root and Health check
@app.get("/api/info")
def read_info():
    return {
        "project": "HE-05: Evidence-Linked Patient Journey",
        "description": "Medical Document Intelligence & Patient Timeline System",
        "status": "operational",
        "version": "1.0.0",
        "docs_url": "/docs",
        "gemini_api_configured": bool(os.environ.get("GEMINI_API_KEY"))
    }


@app.get("/")
def read_root():
    index_file = os.path.join(FRONTEND_DIST, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return read_info()


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "database": "connected",
        "ai_engine": "Gemini API" if os.environ.get("GEMINI_API_KEY") else "Clinical Rule Extractor (Offline Active)"
    }


# Include Routers
app.include_router(patients_router, prefix="/api")
app.include_router(documents_router, prefix="/api")
app.include_router(timeline_router, prefix="/api")
app.include_router(intelligence_router, prefix="/api")
app.include_router(qa_router, prefix="/api")

# Static mount for uploads if directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/static/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Mount frontend dist if built
if os.path.exists(FRONTEND_DIST):
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
