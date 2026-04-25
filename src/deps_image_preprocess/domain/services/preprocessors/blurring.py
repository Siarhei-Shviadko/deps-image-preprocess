from typing import Tuple

import cv2
import numpy as np

from deps_image_preprocess.domain.constants import ImagePreprocessorEnum
from deps_image_preprocess.domain.entities import PreprocessingImage
from deps_image_preprocess.domain.interfaces import IImagePreprocessor


class BlurringPreprocessor(IImagePreprocessor):
    name = ImagePreprocessorEnum.BLURRING
    KERNEL = (3, 3)
    SIGMA = 0

    def apply(self, image: PreprocessingImage) -> PreprocessingImage:
        image.pixels = self._apply_blurring(image.pixels, kernel=self.KERNEL, sigma=self.SIGMA)
        return self._save_transformation_to_image(image, name=self.name, kernel=self.KERNEL, sigma=self.SIGMA)

    @staticmethod
    def _apply_blurring(image: np.ndarray, kernel: Tuple[int, int], sigma: float) -> np.ndarray:
        return cv2.GaussianBlur(image, kernel, sigma)
