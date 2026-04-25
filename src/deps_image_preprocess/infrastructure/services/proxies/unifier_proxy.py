from http import HTTPStatus

from deps_image_preprocess.domain.entities import (
    PreprocessedImage,
    Transformation,
    UnifiedImage,
)
from deps_image_preprocess.domain.exceptions import ServiceProxyError
from deps_image_preprocess.extras.rest_client import (
    BaseRESTClient,
    DEPSApiKeyAuth,
    DEPSTokenAuth,
)
from deps_image_preprocess.infrastructure.access_management import user

__all__ = ["UnifierProxy"]


class UnifierProxy(BaseRESTClient):
    def get_unified_images(self, document_id: int) -> list[UnifiedImage]:
        url = f"{self._base_url}/unified_data/{document_id}"

        response = self._session.get(
            url,
            params={"unified_data_types": "image"},
            timeout=60,
            verify=False,
        )

        if response.status_code != HTTPStatus.OK:
            raise ServiceProxyError(f"Unified data were not fetched. Status code: `{response.status_code}`")

        return [
            UnifiedImage(
                id=element["id"],
                blob_name=element["blobName"],
            )
            for element in response.json()["elements"]
        ]

    def apply_transformations(self, document_id: int, images: list[PreprocessedImage], transformation: Transformation) -> None:
        url = f"{self._base_url}/unified_data/{document_id}/transformations"

        data = {
            "transformation": {
                "name": transformation.name,
                "parameters": {
                    "args": transformation.args,
                    "kwargs": transformation.kwargs,
                },
            },
            "images": [
                {
                    "blobName": image.blob_name,
                    "width": image.width,
                    "height": image.height,
                    "originalImageId": image.original_image_id,
                }
                for image in images
            ],
        }

        response = self._session.patch(
            url,
            json=data,
            timeout=60,
            verify=False,
        )

        if response.status_code != HTTPStatus.NO_CONTENT:
            raise ServiceProxyError(f"Unified data were not updated. Status code: `{response.status_code}`")

    def _set_authentication(self) -> None:
        if self._api_key is not None:
            self._session.auth = DEPSApiKeyAuth(self._api_key)
        else:
            self._session.auth = DEPSTokenAuth(user)
