from fastapi import APIRouter

from .debug import router as debug_router
from .v1 import router as v1_router

router = APIRouter()
router.include_router(v1_router)
router.include_router(debug_router, tags=["Debug"])
