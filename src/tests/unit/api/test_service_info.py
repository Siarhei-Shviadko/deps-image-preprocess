import os
from http import HTTPStatus

from deps_image_preprocess.constants import API_PREFIX


class TestServiceInfo:
    endpoint = API_PREFIX + "/service-info"

    def test_version__got_service_info__return_200(self, client):
        response = client.get(f"{self.endpoint}/version")
        data = response.json()

        assert response.status_code == HTTPStatus.OK
        assert data["buildTag"] == os.getenv("SERVICE_INFO_TAG")
        assert data["buildDate"] == os.getenv("SERVICE_INFO_DATE")
        assert data["commitHash"] == os.getenv("SERVICE_INFO_HASH")
