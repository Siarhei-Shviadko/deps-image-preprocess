from typing import Dict, Optional

import cv2
import numpy as np
from tesserocr import PSM, PyTessBaseAPI

from deps_image_preprocess.domain.constants import (
    ImageOrientationEnum,
    ImagePreprocessorEnum,
)
from deps_image_preprocess.domain.entities import PreprocessingImage
from deps_image_preprocess.domain.interfaces import IImagePreprocessor


class OrientationPreprocessor(IImagePreprocessor):
    name = ImagePreprocessorEnum.ORIENTATION
    minoconf = 13
    rotation_direction = (
        ImageOrientationEnum.DO_NOTHING,
        ImageOrientationEnum.ROTATE_90_COUNTERCLOCKWISE,
        ImageOrientationEnum.ROTATE_180,
        ImageOrientationEnum.ROTATE_90_CLOCKWISE,
    )
    rotation_angles = {
        ImageOrientationEnum.DO_NOTHING: None,
        ImageOrientationEnum.ROTATE_90_COUNTERCLOCKWISE: cv2.ROTATE_90_COUNTERCLOCKWISE,
        ImageOrientationEnum.ROTATE_180: cv2.ROTATE_180,
        ImageOrientationEnum.ROTATE_90_CLOCKWISE: cv2.ROTATE_90_CLOCKWISE,
    }

    def apply(self, image: PreprocessingImage) -> PreprocessingImage:
        orientation = self._find_best_orientation(image.pixels)
        image.pixels = self._apply_orientation(
            image.pixels,
            orientation=self.rotation_angles[orientation],
        )
        return self._save_transformation_to_image(image, name=self.name, orientation=self.rotation_angles[orientation])

    def _find_best_orientation(self, image: np.ndarray) -> ImageOrientationEnum:
        detected_os = self._detect_os(image, "osd")
        if detected_os is None or detected_os["oconfidence"] < 1 and detected_os["script"] == 1:
            orientation = 0
        else:
            if self._is_low_confidence_orientation(detected_os):
                detected_os2 = self._detect_os(image, "eng")
                detected_os = self._select_best_orientation(detected_os, detected_os2)
            orientation = detected_os["orientation"]

        return self.rotation_direction[orientation]

    def _is_low_confidence_orientation(self, detected_os: Dict) -> bool:
        return (
            detected_os["oconfidence"] < 4
            or detected_os["sconfidence"] < 1
            or detected_os["oconfidence"] < self.minoconf
            and (detected_os["sconfidence"] < 4 or detected_os["script"] != 1)
        )

    def _select_best_orientation(self, detected_os: Dict, detected_os2: Dict) -> Dict:
        if detected_os2["oconfidence"] > detected_os["oconfidence"] or (
            detected_os["oconfidence"] < self.minoconf
            and (
                detected_os2["sconfidence"] > detected_os["sconfidence"]
                or detected_os["script"] != 1
                and detected_os2["script"] == 1
            )
        ):
            return detected_os2
        return detected_os

    @staticmethod
    def _detect_os(image: np.ndarray, language: str) -> Dict:
        try:
            channels = image.shape[2]
        except IndexError:
            channels = 1

        with PyTessBaseAPI(lang=language, psm=PSM.AUTO_OSD, init=True) as api:
            api.SetImageBytes(
                image.tobytes(),
                image.shape[1],
                image.shape[0],
                channels,
                channels * image.shape[1],
            )
            detected_os = api.DetectOS()
            api.Clear()
        return detected_os

    @staticmethod
    def _apply_orientation(image: np.ndarray, orientation: Optional[int]) -> np.ndarray:
        if not orientation:
            return image
        return cv2.rotate(image, orientation)
