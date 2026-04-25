from typing import Optional

from deps_image_preprocess.domain.constants import ImagePreprocessorEnum
from deps_image_preprocess.domain.entities import PreprocessingImage, Transformation
from deps_image_preprocess.domain.interfaces import IImagePreprocessService

__all__ = [
    "FakeImagePreprocessService",
]


class FakeImagePreprocessService(IImagePreprocessService):
    def execute(
        self, image: PreprocessingImage, preprocessors: Optional[list[ImagePreprocessorEnum]] = None
    ) -> PreprocessingImage:
        image.applied_transformations.append(Transformation(name="fake", args=[], kwargs={}))

        return image
