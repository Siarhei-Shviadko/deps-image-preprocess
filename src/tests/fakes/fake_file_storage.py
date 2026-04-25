import os
import uuid
from typing import Optional

__all__ = [
    "FakeFileStorage",
]


class FakeFileStorage:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)

        return cls._instance

    def __init__(self):
        if not getattr(self, "_storage", None):
            self._storage: dict[str, bytes] = {}

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

        full_path = os.path.join(file_path, filename)
        self._storage[full_path] = content

        return os.path.join(file_path, filename)

    def download_content(self, file_path: str, storage: Optional[str] = None) -> bytes:
        content = self._storage.get(file_path)
        if not content:
            raise FileNotFoundError(f"File not found: {file_path}")

        return content

    @staticmethod
    def _generate_unique_file_path(file_path: str) -> str:
        """Generates unique file path."""
        root, file_name = os.path.split(file_path)
        _, ext = os.path.splitext(file_name)

        return os.path.join(root, str(uuid.uuid4().hex) + ext)
