import os

import pytest
from fastapi.testclient import TestClient

from deps_image_preprocess.app import create_fastapi
from deps_image_preprocess.domain.constants import ImageExtensionEnum
from deps_image_preprocess.domain.entities import PreprocessingImage
from tests.factories.preprocess import (
    TEST_DATA_PATH,
    PreprocessingImageFactory,
    get_pixel_array_from_file,
)


def get_content_from_pixel_array(image: PreprocessingImage) -> bytes:
    return image.image_content


@pytest.fixture(scope="session")
def fastapi_app():
    yield create_fastapi()


@pytest.fixture(scope="session")
def app(fastapi_app):
    yield fastapi_app.app


@pytest.fixture
def client(fastapi_app):
    with TestClient(fastapi_app) as client:
        yield client


@pytest.fixture
def config(app):
    yield app.config


@pytest.fixture(scope="session")
def services(app):
    yield app.services


@pytest.fixture
def preprocess_service(services):
    yield services.image_preprocess_service()


@pytest.fixture
def preprocessors(services):
    yield services.image_preprocessors


@pytest.fixture
def default_preprocessors(config):
    yield config.preprocess.default_preprocessors()


@pytest.fixture
def png_image():
    return PreprocessingImageFactory()


@pytest.fixture
def jpg_image():
    pixels = get_pixel_array_from_file(f"{TEST_DATA_PATH}image_0.jpg")
    return PreprocessingImageFactory(pixels=pixels, extension=ImageExtensionEnum.JPG)


@pytest.fixture
def tiff_image():
    pixels = get_pixel_array_from_file(f"{TEST_DATA_PATH}image_0.tiff")
    return PreprocessingImageFactory(pixels=pixels, extension=ImageExtensionEnum.TIFF)


@pytest.fixture
def unsupported_image_path():
    return f"{TEST_DATA_PATH}image_0.gif"


@pytest.fixture
def absolute_test_data_path():
    return os.path.abspath(os.path.join(os.path.split(__file__)[0], "data"))
