import cv2
import numpy as np
import pytest

from deps_image_preprocess.domain.constants import ImageExtensionEnum
from deps_image_preprocess.domain.entities import PreprocessingImage
from deps_image_preprocess.domain.exceptions import PreprocessorError
from tests.conftest import get_pixel_array_from_file
from tests.factories.preprocess import PreprocessingImageFactory


def load_jpg_image(image_path: str) -> PreprocessingImage:
    pixels = get_pixel_array_from_file(image_path)
    return PreprocessingImageFactory(extension=ImageExtensionEnum.JPG, pixels=pixels)


@pytest.fixture
def orientation_preprocessor(preprocessors):
    return preprocessors.orientation_preprocessor()


@pytest.fixture
def rotation_preprocessor(preprocessors):
    return preprocessors.rotation_preprocessor()


@pytest.fixture
def grayscaling_preprocessor(preprocessors):
    return preprocessors.grayscaling_preprocessor()


@pytest.fixture
def thresholding_preprocessor(preprocessors):
    return preprocessors.thresholding_preprocessor()


@pytest.fixture
def blurring_preprocessor(preprocessors):
    return preprocessors.blurring_preprocessor()


class TestImagePreprocessors:
    @pytest.mark.parametrize("file_name, expected_angle", [("image_0.jpg", 0), ("image_27.jpg", 27)])
    def test_rotation_preprocessor__apply__rotated_correctly(self, rotation_preprocessor, file_name, expected_angle):
        image_path = f"tests/data/{file_name}"
        processing = load_jpg_image(image_path)

        processed = rotation_preprocessor.apply(processing)
        transformation = processed.applied_transformations[0]
        assert transformation.name == "rotation"
        assert abs(transformation.kwargs["angle"] - expected_angle) < 1e-1
        assert not transformation.args

    @pytest.mark.parametrize(
        "file_name, expected_orientation",
        [
            ("image_0.jpg", None),
            ("image_180.jpg", cv2.ROTATE_180),
            ("image_270.jpg", cv2.ROTATE_90_CLOCKWISE),
        ],
    )
    def test_orientation_preprocessor__apply__orientated_correctly(
        self, orientation_preprocessor, file_name, expected_orientation
    ):
        image_path = f"tests/data/{file_name}"
        processing = load_jpg_image(image_path)

        processed = orientation_preprocessor.apply(processing)
        transformation = processed.applied_transformations[0]
        assert transformation.name == "orientation"
        assert transformation.kwargs["orientation"] == expected_orientation
        assert not transformation.args

    def test_grayscaling_preprocessor__apply__applied(self, grayscaling_preprocessor):
        image_path = f"tests/data/image_0.jpg"
        processing = load_jpg_image(image_path)

        processed = grayscaling_preprocessor.apply(processing)
        transformation = processed.applied_transformations[0]
        assert transformation.name == "grayscaling"
        assert not transformation.args
        assert not transformation.kwargs

    def test_thresholding_preprocessor__apply__applied(self, thresholding_preprocessor):
        image_path = f"tests/data/image_0.jpg"
        processing = load_jpg_image(image_path)

        processed = thresholding_preprocessor.apply(processing)
        transformation = processed.applied_transformations[1]
        assert transformation.name == "thresholding"
        assert transformation.kwargs == {
            "window_size_percent": thresholding_preprocessor.WINDOW_SIZE_PERCENT,
            "local_threshold": thresholding_preprocessor.LOCAL_THRESHOLD,
            "high_value": thresholding_preprocessor.HIGH_VALUE,
        }
        assert not transformation.args

    def test_blurring_preprocessor__apply__applied(self, blurring_preprocessor):
        image_path = f"tests/data/image_0.jpg"
        processing = load_jpg_image(image_path)

        processed = blurring_preprocessor.apply(processing)
        transformation = processed.applied_transformations[0]
        assert transformation.name == "blurring"
        assert transformation.kwargs == {"kernel": blurring_preprocessor.KERNEL, "sigma": blurring_preprocessor.SIGMA}
        assert not transformation.args
