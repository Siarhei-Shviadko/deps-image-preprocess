from http import HTTPStatus
from io import BytesIO

from deps_image_preprocess.constants import API_PREFIX
from deps_image_preprocess.domain.exceptions import ImagePreprocessServiceError
from tests.conftest import get_content_from_pixel_array


class TestPreprocess:
    endpoint = API_PREFIX + "/preprocess"

    def test_preprocess__send_image__preprocessed__return_200(self, client, image_preprocess_service_mock, png_image):
        image_preprocess_service_mock.execute.return_value = png_image

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
        assert data["appliedTransformations"] == []
        assert data["imageContent"]

    def test_preprocess__send_image__preprocess_error_raised__return_400(self, client, image_preprocess_service_mock, png_image):
        image_preprocess_service_mock.execute.side_effect = ImagePreprocessServiceError("test_msg")

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

        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert ImagePreprocessServiceError.code in response.text
        assert "test_msg" in response.text
