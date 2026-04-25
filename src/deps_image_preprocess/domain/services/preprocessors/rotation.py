from copy import deepcopy

import cv2
import numpy as np
from scipy.optimize import minimize_scalar

from deps_image_preprocess.domain.constants import ImagePreprocessorEnum
from deps_image_preprocess.domain.entities import PreprocessingImage
from deps_image_preprocess.domain.interfaces import IImagePreprocessor
from deps_image_preprocess.domain.services.preprocessors.blurring import (
    BlurringPreprocessor,
)
from deps_image_preprocess.domain.services.preprocessors.thresholding import (
    ThresholdingPreprocessor,
)


class RotationPreprocessor(IImagePreprocessor):
    name = ImagePreprocessorEnum.ROTATION

    def __init__(
        self,
        blurring_processor: BlurringPreprocessor,
        thresholding_processor: ThresholdingPreprocessor,
    ):
        self._blurring_processor = blurring_processor
        self._thresholding_processor = thresholding_processor

    def apply(self, image: PreprocessingImage) -> PreprocessingImage:
        binarized_array = self._get_binarized_array(deepcopy(image))
        angle = self._find_best_rotation_angle(binarized_array, threshold_angle=5.0)  # noqa: WPS432
        image.pixels = self._apply_rotation(image.pixels, angle=angle)
        return self._save_transformation_to_image(image, name=self.name, angle=angle)

    def _get_binarized_array(self, image: PreprocessingImage) -> np.ndarray:
        image = self._blurring_processor.apply(image)
        image = self._thresholding_processor.apply(image)
        return image.pixels

    def _find_best_rotation_angle(self, image: np.ndarray, threshold_angle: float = 2.0) -> float:
        def evaluate_rotation_score(angle):  # noqa: WPS430
            rotated_image = self._apply_rotation(image, angle=angle)
            return -(rotated_image.sum(0).std() + rotated_image.sum(1).std())

        best_angle = minimize_scalar(
            evaluate_rotation_score,
            bracket=(-threshold_angle, threshold_angle),
            method="brent",
            options={"maxiter": 15, "xtol": 0.001},
        )
        best_angle = round(best_angle.x, 4)
        if best_angle != 0 and evaluate_rotation_score(best_angle) >= evaluate_rotation_score(0):
            best_angle = 0

        return best_angle

    @staticmethod
    def _apply_rotation(image: np.ndarray, angle: float) -> np.ndarray:
        if angle == 0:
            return image

        rows, cols = image.shape[:2]
        matrix = cv2.getRotationMatrix2D((cols / 2, rows / 2), angle, 1)
        return cv2.warpAffine(image, matrix, (cols, rows), borderValue=(255, 255, 255))
