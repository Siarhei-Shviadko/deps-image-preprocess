import os
from uuid import uuid4

import pytest
from faker import Faker

faker = Faker()


@pytest.fixture(
    params=[
        ("image_0.png", "image.png"),
        ("image_0.png", "image_without_extension"),
        ("image_0.tiff", "template.TIFF"),
        ("image_0.tiff", "template.Tiff"),
        ("image_0.tiff", "template.TIF"),
        ("image_0.tiff", "template.tif"),
        ("pdf_0.pdf", "pdf_file.pdf"),
        ("pdf_0.pdf", "pdf_file_without_extension"),
    ],
)
def upload_files(fake_file_storage, absolute_test_data_path, request):
    original_file_name, path_to_save = request.param
    with open(os.path.join(absolute_test_data_path, original_file_name), "rb") as file:
        fake_file_storage.upload_content(path_to_save, file.read(), generate_unique_filename=False)

    yield path_to_save


@pytest.fixture
def existing_files(fake_file_storage, absolute_test_data_path):
    file_paths = [os.path.join(absolute_test_data_path, path) for path in ["image_0.png", "pdf_0.pdf"]]
    for path in file_paths:
        with open(path, "rb") as file:
            fake_file_storage.upload_content(path, file.read(), generate_unique_filename=False)

    return file_paths


@pytest.fixture
def non_existing_files(fake_file_storage, absolute_test_data_path):
    return [faker.file_name(category="image") for _ in range(2)]


def test_reference_page_processing(upload_files, reference_page_service, fake_file_storage):
    blob_name = upload_files
    for preprocessed_reference_page in reference_page_service.preprocess(uuid4(), [blob_name], "test/"):
        assert fake_file_storage.download_content(preprocessed_reference_page)


@pytest.mark.parametrize(
    "blob_name_save_as",
    [
        "template.TIFF",
        "template.Tiff",
        "template.TIF",
        "template.tif",
    ],
)
def test_reference_page_tiff_case_insensitive_produces_png(
    reference_page_service,
    fake_file_storage,
    absolute_test_data_path,
    blob_name_save_as,
):
    tiff_path = os.path.join(absolute_test_data_path, "image_0.tiff")
    with open(tiff_path, "rb") as f:
        fake_file_storage.upload_content(blob_name_save_as, f.read(), generate_unique_filename=False)

    result = reference_page_service.preprocess(uuid4(), [blob_name_save_as], "test/")
    assert len(result) == 1
    assert result[0].endswith(".png")
    assert fake_file_storage.download_content(result[0])


def test_reference_page_reverting(reference_page_service, fake_dep, existing_files, non_existing_files):
    blob_names = existing_files + non_existing_files
    with pytest.raises(Exception):
        reference_page_service.preprocess(uuid4(), blob_names, "test/")

    assert fake_dep.last_published.events
    assert len(fake_dep.last_published.events[0].file_paths) == 5
