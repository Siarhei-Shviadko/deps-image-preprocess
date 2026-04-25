import cv2
import numpy as np

from deps_image_preprocess.domain.constants import ImagePreprocessorEnum
from deps_image_preprocess.domain.entities import PreprocessingImage
from deps_image_preprocess.domain.interfaces import IImagePreprocessor


class GrayscalingPreprocessor(IImagePreprocessor):
    name = ImagePreprocessorEnum.GRAYSCALING

    def apply(self, image: PreprocessingImage) -> PreprocessingImage:
        image.pixels = self._apply_grayscaling(image.pixels)
        return self._save_transformation_to_image(image, name=self.name)

    @staticmethod
    def _apply_grayscaling(image: np.ndarray) -> np.ndarray:
        return cv2.cvtColor(image, code=cv2.COLOR_BGR2GRAY)
