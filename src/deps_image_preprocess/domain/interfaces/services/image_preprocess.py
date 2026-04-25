from abc import ABC, abstractmethod
from typing import Optional

from deps_image_preprocess.domain.constants import ImagePreprocessorEnum
from deps_image_preprocess.domain.entities import PreprocessingImage

__all__ = [
    "IImagePreprocessService",
]


class IImagePreprocessService(ABC):
    @abstractmethod
    def execute(
        self, image: PreprocessingImage, preprocessors: Optional[list[ImagePreprocessorEnum]] = None
    ) -> PreprocessingImage:
        pass
