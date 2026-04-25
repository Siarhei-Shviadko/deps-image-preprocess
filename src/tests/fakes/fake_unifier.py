import json
from uuid import uuid4

from deps_image_preprocess.domain.entities import (
    PreprocessedImage,
    Transformation,
    UnifiedImage,
)
from deps_image_preprocess.domain.exceptions import ServiceProxyError

from .fake_file_storage import FakeFileStorage

__all__ = [
    "FakeUnifier",
]


class FakeUnifier:
    _path = "unified_data"

    def __init__(self, fake_file_storage: FakeFileStorage):
        self._file_storage = fake_file_storage

    def get_unified_images(self, document_id: int) -> list[UnifiedImage]:
        unified_data = self._get_unified_data(document_id)
        return [UnifiedImage(id=element["id"], blob_name=element["blobName"]) for element in unified_data["elements"]]

    def apply_transformations(self, document_id: int, images: list[PreprocessedImage], transformation: Transformation) -> None:
        unified_data = self._get_unified_data(document_id)
        for image in images:
            unified_data["elements"].append(
                {
                    "id": uuid4().hex,
                    "blobName": image.blob_name,
                }
            )
        self._file_storage.upload_content(
            f"{self._path}/{document_id}.json",
            json.dumps(unified_data).encode(),
            generate_unique_filename=False,
        )

    def _get_unified_data(self, document_id: int) -> dict:
        try:
            return json.loads(self._file_storage.download_content(f"{self._path}/{document_id}.json"))
        except FileNotFoundError:
            raise ServiceProxyError
