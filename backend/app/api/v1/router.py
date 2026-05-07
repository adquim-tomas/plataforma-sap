from fastapi import APIRouter

from app.api.v1.endpoints import auth, audit, health, uploads

router = APIRouter(prefix="/api/v1")

router.include_router(auth.router)
router.include_router(audit.router)
router.include_router(health.router)
router.include_router(uploads.router)
