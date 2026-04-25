from typing import Union

import numpy as np

from deps_image_preprocess.domain.constants import ImagePreprocessorEnum
from deps_image_preprocess.domain.entities import PreprocessingImage
from deps_image_preprocess.domain.interfaces import IImagePreprocessor
from deps_image_preprocess.domain.services.preprocessors.grayscaling import (
    GrayscalingPreprocessor,
)


class ThresholdingPreprocessor(IImagePreprocessor):
    name = ImagePreprocessorEnum.THRESHOLDING
    WINDOW_SIZE_PERCENT = 0.03
    LOCAL_THRESHOLD = 0.15
    HIGH_VALUE = 255
    DEFAULT_THRESHOLD = 128
    DEFAULT_BACKGROUND_VALUE = 255

    def __init__(self, grayscaling_processor: GrayscalingPreprocessor):
        self._grayscaling_processor = grayscaling_processor

    def apply(self, image: PreprocessingImage) -> PreprocessingImage:
        if not self._is_grayscaled(image):
            image = self._grayscaling_processor.apply(image)
        image.pixels = self._apply_thresholding(
            image.pixels,
            window_size_percent=self.WINDOW_SIZE_PERCENT,
            local_threshold=self.LOCAL_THRESHOLD,
            high_value=self.HIGH_VALUE,
        )
        return self._save_transformation_to_image(
            image,
            name=self.name,
            window_size_percent=self.WINDOW_SIZE_PERCENT,
            local_threshold=self.LOCAL_THRESHOLD,
            high_value=self.HIGH_VALUE,
        )

    @classmethod
    def _apply_thresholding(
        cls, image: np.ndarray, window_size_percent: float, local_threshold: float, high_value: int
    ) -> np.ndarray:
        return cls._apply_threshold(image, cls._bradley_roth_threshold(image, window_size_percent, local_threshold), high_value)

    @staticmethod
    def _is_grayscaled(image: PreprocessingImage) -> bool:
        return any(transformation.name == ImagePreprocessorEnum.GRAYSCALING for transformation in image.applied_transformations)

    @staticmethod
    def _apply_threshold(
        img: np.ndarray, threshold: Union[int, np.ndarray] = DEFAULT_THRESHOLD, wp_val: int = DEFAULT_BACKGROUND_VALUE
    ) -> np.ndarray:
        """Obtain a binary image based on a given global threshold or
        a set of local thresholds.

        @param img: The input image.
        @param threshold: The global or local thresholds corresponding to each pixel of the image.
        @param wp_val: The value assigned to foreground pixels (white pixels).

        @return: A binary image.
        """
        return ((img >= threshold) * wp_val).astype(np.uint8)

    @classmethod
    def _bradley_roth_threshold(cls, img: np.ndarray, w_size: Union[int, float], t: float) -> np.ndarray:
        """
        Code based on https://github.com/manuelaguadomtz/pythreshold/
        with updates to make it work with recent version of numpy.

        Runs the Bradley-Roth thresholding algorithm.

        Reference:
        Bradley, D., & Roth, G. (2007). Adaptive thresholding
        using the integral image. Journal of Graphics Tools, 12(2), 13-21.

        @param img: The input image
        @param w_size: The size of the local window to compute each pixel threshold.
        Should be and odd value in pixels or percent of image size.
        @param t: Used to verify is each pixel is 't' percent lower than the local average.
        It should be a normalized value in the range [0, 1].

        @return: The estimated local threshold for each pixel
        """
        w_size_int = int(w_size)
        if w_size < 1:
            w_size_int = round(max(img.shape[:2]) * w_size)
        if w_size_int % 2 == 0:
            w_size_int += 1

        # Obtaining rows and cols
        rows, cols = img.shape

        integ = cls._compute_integral_image(img)
        x1, x2, y1, y2 = cls._obtain_local_coordinates(rows, cols, w_size_int)

        # Obtaining local areas size
        l_size = (y2 - y1) * (x2 - x1)

        # Computing sums
        sums = integ[y2, x2] - integ[y2, x1]
        sums = sums - integ[y1, x2] + integ[y1, x1]

        # Computing local means
        means = sums / l_size

        return means * (1 - t)

    @staticmethod
    def _compute_integral_image(img: np.ndarray) -> np.ndarray:
        # Computing integral image
        # Leaving first row and column in zero for convenience

        rows, cols = img.shape
        i_rows, i_cols = rows + 1, cols + 1

        img_float = img.astype(np.float64)
        integ = np.zeros((i_rows, i_cols), np.float64)
        col_cumsum = np.cumsum(img_float, axis=0)
        integ[1:, 1:] = np.cumsum(col_cumsum, axis=1)

        return integ

    @staticmethod
    def _obtain_local_coordinates(rows: int, cols: int, w_size: int) -> tuple:
        i_rows, i_cols = rows + 1, cols + 1

        # Defining grid
        xi = np.arange(1, i_cols)
        yi = np.arange(1, i_rows)
        x, y = np.meshgrid(xi, yi)

        # Obtaining local coordinates
        hw_size = w_size // 2
        x1 = (x - hw_size).clip(1, cols) - 1
        x2 = (x + hw_size).clip(1, cols)
        y1 = (y - hw_size).clip(1, rows) - 1
        y2 = (y + hw_size).clip(1, rows)

        return x1, x2, y1, y2
