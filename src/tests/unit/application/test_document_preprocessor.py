import json
import os

import pytest
from faker import Faker
from pytest_factoryboy import register

from tests.factories.unified_image import UnifiedImageFactory

fake = Faker()


register(UnifiedImageFactory)


@pytest.fixture
def document_id():
    yield fake.pyint(min_value=1)


@pytest.fixture(
    params=[
        "image_0.png",
        "image_0.jpg",
        "image_27.png",
        "image_27.jpg",
    ],
)
def image_content(absolute_test_data_path, request):
    with open(os.path.join(absolute_test_data_path, request.param), "rb") as file:
        yield file.read()


@pytest.fixture
def gen_unified_data(document_id, image_content, fake_file_storage, unified_image_factory):
    images = unified_image_factory.create_batch(2)
    unified_data = {"elements": []}
    for image in images:
        fake_file_storage.upload_content(
            image.blob_name,
            image_content,
            generate_unique_filename=False,
        )
        unified_data["elements"].append({"id": image.id, "blobName": image.blob_name})
    fake_file_storage.upload_content(
        f"unified_data/{document_id}.json",
        json.dumps(unified_data).encode(),
        generate_unique_filename=False,
    )

    return unified_data["elements"]


def test_document_images_preprocessed(document_id, document_preprocessor_service, gen_unified_data, fake_unifier):
    document_preprocessor_service.preprocess(document_id)
    assert len(fake_unifier.get_unified_images(document_id)) == len(gen_unified_data) * 2


def test_document_images_not_preprocessed(
    document_id,
    document_preprocessor_service,
    gen_unified_data,
    fake_file_storage,
    fake_dep,
):
    blob_name = gen_unified_data[-1]["blobName"]
    fake_file_storage._storage.pop(blob_name)
    with pytest.raises(Exception):
        document_preprocessor_service.preprocess(document_id)

    assert fake_dep.last_published.events
    assert len(fake_dep.last_published.events[0].file_paths) == len(gen_unified_data) - 1
