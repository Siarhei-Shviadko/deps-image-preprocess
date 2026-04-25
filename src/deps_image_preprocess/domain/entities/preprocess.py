from dataclasses import dataclass, field
from imghdr import what
from typing import Any, ClassVar, Optional

import cv2
import numpy as np

from deps_image_preprocess.domain.constants import ImageExtensionEnum
from deps_image_preprocess.domain.exceptions import PreprocessingImageError


@dataclass
class Transformation:
    name: str
    args: list[Any] = field(default_factory=list)
    kwargs: dict[str, Any] = field(default_factory=dict)


class _TransformationList(list[Transformation]):
    def append(self, obj: object) -> None:  # noqa: WPS110
        if not isinstance(obj, Transformation):
            raise ValueError("Not a transformation")

        super().append(obj)

    def combine(self) -> Transformation:
        if not self:
            raise LookupError("Doesn't contain any transformations")

        return Transformation(
            name=", ".join(transformation.name for transformation in self),
            args=sum([transformation.args for transformation in self], start=[]),
            kwargs={key: value for transformation in self for key, value in transformation.kwargs.items()},
        )


@dataclass
class PreprocessingImage:
    pixels: np.ndarray
    applied_transformations: _TransformationList = field(default_factory=_TransformationList)
    extension: Optional[ImageExtensionEnum] = None
    cv_encode_params_mapping: ClassVar = {
        ImageExtensionEnum.PNG.value: [cv2.IMWRITE_PNG_COMPRESSION, 6],
        ImageExtensionEnum.JPG.value: [cv2.IMWRITE_JPEG_OPTIMIZE, 1],
        ImageExtensionEnum.JPEG.value: [cv2.IMWRITE_JPEG_OPTIMIZE, 1],
        ImageExtensionEnum.TIFF.value: [cv2.IMWRITE_TIFF_COMPRESSION, 5],
        ImageExtensionEnum.TIF.value: [cv2.IMWRITE_TIFF_COMPRESSION, 5],
    }

    @property
    def image_content(self) -> bytes:
        cv_extension = f".{self.extension or ImageExtensionEnum.PNG}"
        encode_params = self.cv_encode_params_mapping[cv_extension[1:]]
        return bytes(cv2.imencode(cv_extension, self.pixels, encode_params)[1])

    @property
    def shape(self) -> tuple[int, int]:
        return self.pixels.shape[:2]

    @classmethod
    def from_image_content(cls, image_content: bytes, *, extension: Optional[ImageExtensionEnum] = None) -> "PreprocessingImage":
        image_array = np.asarray(bytearray(image_content), dtype="uint8")
        pixels = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

        return PreprocessingImage(
            pixels=pixels,
            extension=extension if extension is not None else cls._determine_extension(image_content),
        )

    @staticmethod
    def _determine_extension(image_content: bytes) -> ImageExtensionEnum:
        ext = what(None, image_content)
        if ext not in list(ImageExtensionEnum):
            raise PreprocessingImageError(f"Got unsupported image extension: {ext}")
        return ext  # type: ignore


@dataclass
class PreprocessedImage:
    blob_name: str
    width: int
    height: int
    original_image_id: str
