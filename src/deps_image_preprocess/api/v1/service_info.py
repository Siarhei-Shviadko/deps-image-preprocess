from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from deps_image_preprocess.api.models.build_info import BuildInfoModel
from deps_image_preprocess.containers import Core

router = APIRouter(prefix="/service-info")


@router.get("/version", response_model=BuildInfoModel)
@inject
def get_build_info(build_info=Depends(Provide[Core.build_info])):
    return BuildInfoModel(**build_info)
