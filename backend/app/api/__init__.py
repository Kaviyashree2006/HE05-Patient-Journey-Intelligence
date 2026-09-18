from app.api.patients import router as patients_router
from app.api.documents import router as documents_router
from app.api.timeline import router as timeline_router
from app.api.intelligence import router as intelligence_router
from app.api.qa import router as qa_router

__all__ = [
    "patients_router",
    "documents_router",
    "timeline_router",
    "intelligence_router",
    "qa_router"
]
