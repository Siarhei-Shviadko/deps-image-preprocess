from base64 import b64decode
from http import HTTPStatus
from io import BytesIO

from deps_image_preprocess.constants import API_PREFIX
from deps_image_preprocess.domain.exceptions import PreprocessingImageError
from deps_image_preprocess.domain.services.preprocessors import (
    BlurringPreprocessor,
    GrayscalingPreprocessor,
    OrientationPreprocessor,
    RotationPreprocessor,
    ThresholdingPreprocessor,
)
from tests.conftest import get_content_from_pixel_array
from tests.factories.preprocess import TEST_DATA_PATH, load_image_bytes


class TestPreprocess:
    endpoint = API_PREFIX + "/preprocess"

    def test_preprocess__send_png_image__return_200(self, client, png_image):
        expected_transformations = [
            {"name": RotationPreprocessor.name.value, "args": [], "kwargs": {"angle": 0.0}},
            {"name": OrientationPreprocessor.name.value, "args": [], "kwargs": {"orientation": None}},
        ]

        response = client.post(
            self.endpoint,
            files={
                "imageContent": (
                    "test.png",
                    BytesIO(get_content_from_pixel_array(png_image)),
                )
            },
            data={"extension": "png"},
        )
        data = response.json()

        assert response.status_code == HTTPStatus.OK
        assert data["appliedTransformations"] == expected_transformations
        assert data["imageContent"]

    def test_preprocess__send_jpg_image__return_200(self, client, jpg_image):
        expected_transformations = [
            {"name": RotationPreprocessor.name.value, "args": [], "kwargs": {"angle": 0.0}},
            {"name": OrientationPreprocessor.name.value, "args": [], "kwargs": {"orientation": None}},
        ]

        response = client.post(
            self.endpoint,
            files={
                "imageContent": (
                    "test.jpg",
                    BytesIO(get_content_from_pixel_array(jpg_image)),
                )
            },
            data={"extension": "jpg"},
        )
        data = response.json()

        assert response.status_code == HTTPStatus.OK
        assert data["appliedTransformations"] == expected_transformations
        assert data["imageContent"]

    def test_preprocess__send_jpg_image__send_no_extension__return_200(self, client, jpg_image):
        expected_transformations = [
            {"name": RotationPreprocessor.name.value, "args": [], "kwargs": {"angle": 0.0}},
            {"name": OrientationPreprocessor.name.value, "args": [], "kwargs": {"orientation": None}},
        ]

        response = client.post(
            self.endpoint,
            files={
                "imageContent": (
                    "test.jpg",
                    BytesIO(get_content_from_pixel_array(jpg_image)),
                )
            },
        )
        data = response.json()

        assert response.status_code == HTTPStatus.OK
        assert data["appliedTransformations"] == expected_transformations
        assert data["imageContent"]

    def test_preprocess__send_png_image__send_no_extension__return_200(self, client, png_image):
        expected_transformations = [
            {"name": RotationPreprocessor.name.value, "args": [], "kwargs": {"angle": 0.0}},
            {"name": OrientationPreprocessor.name.value, "args": [], "kwargs": {"orientation": None}},
        ]

        response = client.post(
            self.endpoint,
            files={
                "imageContent": (
                    "test.png",
                    BytesIO(get_content_from_pixel_array(png_image)),
                )
            },
        )
        data = response.json()

        assert response.status_code == HTTPStatus.OK
        assert data["appliedTransformations"] == expected_transformations
        assert data["imageContent"]

    def test_preprocess__send_non_default_preprocessors__return_200(self, client, png_image):
        expected_transformations = [
            {
                "args": [],
                "kwargs": {"kernel": list(BlurringPreprocessor.KERNEL), "sigma": BlurringPreprocessor.SIGMA},
                "name": BlurringPreprocessor.name.value,
            },
            {"args": [], "kwargs": {}, "name": GrayscalingPreprocessor.name},
            {
                "args": [],
                "kwargs": {
                    "window_size_percent": ThresholdingPreprocessor.WINDOW_SIZE_PERCENT,
                    "local_threshold": ThresholdingPreprocessor.LOCAL_THRESHOLD,
                    "high_value": ThresholdingPreprocessor.HIGH_VALUE,
                },
                "name": ThresholdingPreprocessor.name.value,
            },
        ]

        response = client.post(
            self.endpoint,
            files={
                "imageContent": (
                    "test.png",
                    BytesIO(get_content_from_pixel_array(png_image)),
                )
            },
            data={"extension": "png", "preprocessors": ["blurring", "grayscaling", "thresholding"]},
        )
        data = response.json()

        assert response.status_code == HTTPStatus.OK
        assert data["appliedTransformations"] == expected_transformations
        assert data["imageContent"]

    def test_preprocess__send_image_w_unsupported_extension__return_400(self, client, unsupported_image_path):
        response = client.post(
            self.endpoint,
            files={
                "imageContent": (
                    "test.gif",
                    BytesIO(load_image_bytes(unsupported_image_path)),
                )
            },
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert PreprocessingImageError.code in response.text

    def test_preprocess__send_tiff__return_200(self, client, tiff_image):
        response = client.post(
            self.endpoint,
            files={
                "imageContent": (
                    "test.tiff",
                    BytesIO(get_content_from_pixel_array(tiff_image)),
                )
            },
        )

        assert response.status_code == HTTPStatus.OK

    def test_preprocess__send_png_image__rotate_correctly__return_200(self, client):
        response = client.post(
            self.endpoint,
            files={
                "imageContent": (
                    "test.png",
                    BytesIO(load_image_bytes(f"{TEST_DATA_PATH}image_27.png")),
                )
            },
        )

        assert response.status_code == HTTPStatus.OK

        data = response.json()
        content = data["imageContent"]

        with open(f"{TEST_DATA_PATH}expected/rotated.png", "rb") as f:
            assert f.read() == b64decode(content)

    def test_preprocess__send_jpg_image__orient_correctly__return_200(self, client):
        response = client.post(
            self.endpoint,
            files={
                "imageContent": (
                    "test.jpg",
                    BytesIO(load_image_bytes(f"{TEST_DATA_PATH}image_180.jpg")),
                )
            },
        )

        assert response.status_code == HTTPStatus.OK

        data = response.json()
        content = data["imageContent"]

        with open(f"{TEST_DATA_PATH}expected/oriented.jpg", "rb") as f:
            assert f.read() == b64decode(content)
