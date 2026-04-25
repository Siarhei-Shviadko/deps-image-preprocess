import pytest

from tests.fakes import (
    FakeDomainEventPublisher,
    FakeFileStorage,
    FakeImagePreprocessService,
    FakeUnifier,
)


@pytest.fixture
def image_preprocess_service_mock(services, mocker):
    mock = mocker.Mock(services.image_preprocess_service.cls)
    services.image_preprocess_service.override(mock)

    yield mock

    services.image_preprocess_service.reset_override()


@pytest.fixture
def fake_file_storage(services):
    with services.file_storage.override(FakeFileStorage()) as storage:
        yield storage()


@pytest.fixture
def fake_image_preprocess(services):
    with services.image_preprocess_service.override(FakeImagePreprocessService()) as service:
        yield service()


@pytest.fixture(scope="session")
def fake_dep(app):
    with app.domain_event_publishers.publisher.override(FakeDomainEventPublisher()) as dep:
        yield dep()


@pytest.fixture
def reference_page_service(app, fake_file_storage, fake_image_preprocess, fake_dep):
    yield app.reference_page_service()


@pytest.fixture
def fake_unifier(services, fake_file_storage):
    with services.unifier.override(FakeUnifier(fake_file_storage)) as storage:
        yield storage()


@pytest.fixture
def document_preprocessor_service(app, fake_unifier, fake_file_storage, fake_image_preprocess, fake_dep):
    yield app.document_preprocessor_service()
