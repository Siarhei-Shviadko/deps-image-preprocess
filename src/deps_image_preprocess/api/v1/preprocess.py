from typing import Optional

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, File, Form

from deps_image_preprocess.api.models import PreprocessedImageResponseModel
from deps_image_preprocess.containers import Services
from deps_image_preprocess.domain.constants import (
    ImageExtensionEnum,
    ImagePreprocessorEnum,
)
from deps_image_preprocess.domain.entities import PreprocessingImage
from deps_image_preprocess.domain.interfaces import IImagePreprocessService

router = APIRouter()


@router.post("/preprocess", response_model=PreprocessedImageResponseModel)
@inject
def preprocess_image(
    image_content: bytes = File(..., alias="imageContent"),
    extension: Optional[ImageExtensionEnum] = Form(None),
    preprocessors: Optional[list[ImagePreprocessorEnum]] = Form(None),
    image_preprocess_service: IImagePreprocessService = Depends(Provide[Services.image_preprocess_service]),
):
    preprocessed = image_preprocess_service.execute(
        image=PreprocessingImage.from_image_content(image_content, extension=extension),
        preprocessors=preprocessors,
    )
    return PreprocessedImageResponseModel.from_domain(preprocessed)
