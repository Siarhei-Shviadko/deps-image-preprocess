from base64 import b64encode
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from deps_image_preprocess.domain.entities import PreprocessingImage

DEFAULT_IMAGE_EXTENSION = ".png"


class AppliedTransformationModel(BaseModel):
    name: str
    args: list[Any] = Field(default_factory=list)
    kwargs: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class PreprocessedImageResponseModel(BaseModel):
    image_content: bytes = Field(..., alias="imageContent")
    applied_transformations: list[AppliedTransformationModel] = Field(default_factory=list, alias="appliedTransformations")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    @classmethod
    def from_domain(cls, image: PreprocessingImage) -> "PreprocessedImageResponseModel":
        return cls(image_content=b64encode(image.image_content), applied_transformations=image.applied_transformations)
