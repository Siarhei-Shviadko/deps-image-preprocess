import logging
from typing import Optional

from deps_image_preprocess.domain.constants import ImagePreprocessorEnum
from deps_image_preprocess.domain.entities import PreprocessingImage
from deps_image_preprocess.domain.exceptions import (
    ImagePreprocessServiceError,
    PreprocessorError,
)
from deps_image_preprocess.domain.interfaces import (
    IImagePreprocessor,
    IImagePreprocessService,
)

__all__ = [
    "ImagePreprocessService",
]

_logger = logging.getLogger(__name__)


class ImagePreprocessService(IImagePreprocessService):
    def __init__(
        self,
        available_preprocessors: dict[ImagePreprocessorEnum, IImagePreprocessor],
        default_preprocessors: list[ImagePreprocessorEnum],
    ):
        self._available_preprocessors = available_preprocessors
        self._default_preprocessors = default_preprocessors

    def execute(
        self, image: PreprocessingImage, preprocessors: Optional[list[ImagePreprocessorEnum]] = None
    ) -> PreprocessingImage:
        preprocessors_to_apply = self._get_preprocessors_to_apply(preprocessors)
        return self._apply_preprocessors(image, preprocessors_to_apply)

    def _get_preprocessors_to_apply(
        self, image_preprocessors: Optional[list[ImagePreprocessorEnum]]
    ) -> dict[ImagePreprocessorEnum, IImagePreprocessor]:
        if image_preprocessors is None:
            image_preprocessors = self._default_preprocessors

        to_apply = {}
        for preprocessor_name in image_preprocessors:
            preprocessor = self._available_preprocessors.get(preprocessor_name)
            if preprocessor:
                to_apply[preprocessor_name] = preprocessor
            else:
                raise ImagePreprocessServiceError(f"Got '{preprocessor_name}' preprocessor, but it's not available")
        return to_apply

    def _apply_preprocessors(
        self, image: PreprocessingImage, preprocessors: dict[ImagePreprocessorEnum, IImagePreprocessor]
    ) -> PreprocessingImage:
        if not preprocessors:
            return image
        for preprocessor_name, preprocessor in preprocessors.items():
            image = self._apply_preprocessor(image, preprocessor_name, preprocessor)
        return image

    @staticmethod
    def _apply_preprocessor(
        image: PreprocessingImage, preprocessor_name: ImagePreprocessorEnum, preprocessor: IImagePreprocessor
    ) -> PreprocessingImage:
        try:
            image = preprocessor.apply(image)
        except PreprocessorError as e:
            raise ImagePreprocessServiceError(f"Preprocessing by {preprocessor_name} has failed: {e}")
        _logger.info(
            "Preprocessor '%s' has been applied successfully",
            preprocessor_name,
        )
        return image
