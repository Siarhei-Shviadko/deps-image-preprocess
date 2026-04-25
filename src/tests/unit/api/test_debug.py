from http import HTTPStatus

import pytest

from deps_image_preprocess.constants import BASE_API_PREFIX


def test_healthcheck___return_200(client):
    response = client.get(f"{BASE_API_PREFIX}/healthcheck")

    assert response.status_code == HTTPStatus.OK


def test_debug___error_raised(client):
    with pytest.raises(ValueError):
        response = client.get(f"{BASE_API_PREFIX}/debug/500")
