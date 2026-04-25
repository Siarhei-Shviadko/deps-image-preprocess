import cv2
import factory
import numpy as np

from deps_image_preprocess.domain.constants import ImageExtensionEnum
from deps_image_preprocess.domain.entities import PreprocessingImage

TEST_DATA_PATH = "tests/data/"


def load_image_bytes(path: str) -> bytes:
    with open(path, "rb") as image:
        return image.read()


def get_pixel_array_from_bytes(image_content: bytes) -> np.ndarray:
    image_array = np.asarray(bytearray(image_content), dtype="uint8")
    return cv2.imdecode(image_array, cv2.IMREAD_COLOR)


def get_pixel_array_from_file(path: str):
    image_content = load_image_bytes(path)
    return get_pixel_array_from_bytes(image_content)


def load_png_pixels() -> np.ndarray:
    return get_pixel_array_from_file(f"{TEST_DATA_PATH}image_0.png")


class PreprocessingImageFactory(factory.Factory):
    class Meta:
        model = PreprocessingImage

    pixels: np.ndarray = factory.LazyFunction(load_png_pixels)
    extension: ImageExtensionEnum = ImageExtensionEnum.PNG
