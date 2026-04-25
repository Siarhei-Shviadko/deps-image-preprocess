from fastapi import APIRouter

from deps_image_preprocess.constants import V1_PREFIX

from .preprocess import router as preprocess_router
from .service_info import router as service_info_router

router = APIRouter(prefix=V1_PREFIX)
router.include_router(preprocess_router, tags=["Preprocess"])
router.include_router(service_info_router, tags=["Service Info"])
