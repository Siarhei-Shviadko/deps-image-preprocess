import json
import os
import tempfile
import uuid
from io import BytesIO
from typing import Any, Dict, Optional

from ..drivers_api import AuthDriverMixin
from .exceptions import FileStorageRequestError

__all__ = ["StorageControllerService"]


class StorageControllerService(AuthDriverMixin):
    def __init__(
        self,
        file_storage_url: str,
        verify_ssl: bool = False,
        storage: Optional[str] = None,
        access_token: Optional[str] = None,
    ):
        super(StorageControllerService, self).__init__(access_token=access_token)
        self._file_storage_url = file_storage_url
        self._storage = storage
        self._verify_ssl = verify_ssl

    def upload_file(self, file_path: str, source_path: str, storage: Optional[str] = None) -> str:
        file_path, filename = os.path.split(file_path)
        with open(source_path, "rb") as fp:
            return self._upload_file(
                file_path,
                filename,
                fp,
                storage or self._storage,
                replace_if_exists=True,
            )

    def upload_content(
        self,
        file_path: str,
        content: bytes,
        storage: Optional[str] = None,
        generate_unique_filename: bool = True,
    ) -> str:
        if generate_unique_filename:
            file_path = self._generate_unique_file_path(file_path)
        file_path, filename = os.path.split(file_path)

        return self._upload_file(
            file_path,
            filename,
            BytesIO(content),
            storage or self._storage,
            replace_if_exists=True,
        )

    def download_file(self, file_path: str, destination_path: str, storage: Optional[str] = None) -> None:
        content = self.download_content(file_path, storage or self._storage)

        with open(destination_path, "wb") as fp:
            fp.write(content)

    def download_content(self, file_path: str, storage: Optional[str] = None) -> bytes:
        response = self._session.get(
            self._get_url(file_path),
            params={"storage": storage or self._storage},
            verify=self._verify_ssl,
        )
        self._handle_response_errors(response)
        content = response.content
        return content

    def delete_file(self, file_path: str, storage: Optional[str] = None) -> None:
        response = self._session.delete(
            self._get_url(file_path),
            data={"storage": storage or self._storage},
            verify=self._verify_ssl,
        )
        self._handle_response_errors(response)

    def _upload_file(
        self,
        file_path: str,
        filename: str,
        file_object,
        storage: Optional[str],
        replace_if_exists=False,
    ):
        file = {
            "file": (filename, file_object),
        }
        response = self._session.post(
            self._get_url(file_path),
            files=file,
            data={"replaceIfExists": replace_if_exists, "storage": storage},
            verify=self._verify_ssl,
        )
        self._handle_response_errors(response)

        response_json = response.json()
        return response_json["path"]

    def _get_url(self, file_path):
        return "/".join((self._file_storage_url, file_path)).rstrip("/")

    @staticmethod
    def _handle_response_errors(response):
        if not response.ok:
            raise FileStorageRequestError(f"File storage service returned {response.status_code} code: {response.text}")

    @staticmethod
    def _generate_unique_file_path(file_path: str) -> str:
        root, file_name = os.path.split(file_path)
        _, ext = os.path.splitext(file_name)

        return os.path.join(root, str(uuid.uuid4().hex) + ext)

    def load_metadata(self, file_path: str, storage: Optional[str] = None) -> Dict[str, Any]:
        metadata_path = self._get_metadata_path(file_path)

        try:
            content = self.download_content(metadata_path, storage or self._storage)
            json_str = content.decode("utf8")
            metadata = json.loads(json_str)
        except FileStorageRequestError:
            metadata = {}

        return metadata

    def upload_metadata(
        self,
        file_path: str,
        metadata: Dict[str, Any],
        storage: Optional[str] = None,
    ) -> None:
        metadata_path = self._get_metadata_path(file_path)

        file_metadata = self.load_metadata(file_path, storage=storage)
        file_metadata.update(metadata)

        json_str = json.dumps(file_metadata)
        content = json_str.encode("utf8")

        with tempfile.NamedTemporaryFile() as fp:
            fp.write(content)
            fp.flush()
            self.upload_file(metadata_path, fp.name, storage or self._storage)

    def delete_metadata(self, file_path: str, storage: Optional[str] = None) -> None:
        metadata_path = self._get_metadata_path(file_path)
        self.delete_file(metadata_path, storage or self._storage)

    @staticmethod
    def _get_metadata_path(file_path: str) -> str:
        dir_path, filename = os.path.split(file_path)
        filename, _ = os.path.splitext(filename)

        metadata_filename = "metadata_{}.json".format(filename)
        metadata_path = os.path.join(dir_path, metadata_filename)

        return metadata_path
