from logging import getLogger
from os import path
from typing import Iterable, Optional
from uuid import uuid4

from deps_message_flow.events.publisher import DomainEventPublisher

from deps_image_preprocess.constants import DOCUMENTS_AGGREGATE
from deps_image_preprocess.domain.constants import ImagePreprocessorEnum
from deps_image_preprocess.domain.entities import (
    PreprocessedImage,
    PreprocessingImage,
    UnifiedImage,
)
from deps_image_preprocess.domain.events import DeleteFiles
from deps_image_preprocess.domain.interfaces import IImagePreprocessService
from deps_image_preprocess.extras.storage import StorageControllerService
from deps_image_preprocess.infrastructure.services.proxies import UnifierProxy

__all__ = [
    "DocumentPreprocessorService",
]

_logger = getLogger(__name__)


class DocumentPreprocessorService:
    def __init__(
        self,
        unifier_proxy: UnifierProxy,
        file_storage: StorageControllerService,
        image_preprocess_service: IImagePreprocessService,
        event_publisher: DomainEventPublisher,
        default_preprocessors: Iterable[ImagePreprocessorEnum] = (
            ImagePreprocessorEnum.ROTATION,
            ImagePreprocessorEnum.ORIENTATION,
        ),
    ):
        self._unifier = unifier_proxy
        self._file_storage = file_storage
        self._image_preprocess = image_preprocess_service
        self._event_publisher = event_publisher
        self._default_preprocessors = list(default_preprocessors)

    def preprocess(self, document_id: int, preprocessors: Optional[list[ImagePreprocessorEnum]] = None) -> None:
        unified_images = self._unifier.get_unified_images(document_id)
        if not unified_images:
            return

        preprocessed_images = []

        try:
            for unified_image in unified_images:
                preprocessed_image = self._preprocess_image(unified_image, preprocessors)
                blob_name = self._upload_image(unified_image.blob_name, preprocessed_image)
                preprocessed_images.append((blob_name, unified_image.id, preprocessed_image))

            self._apply_transformations(document_id, preprocessed_images)
        except Exception:
            self._revert_preprocessed_images(document_id, [i[0] for i in preprocessed_images])
            raise

    def _preprocess_image(
        self,
        unified_image: UnifiedImage,
        preprocessors: Optional[list[ImagePreprocessorEnum]] = None,
    ) -> PreprocessingImage:
        blob_content = self._file_storage.download_content(unified_image.blob_name)
        return self._image_preprocess.execute(
            image=PreprocessingImage.from_image_content(blob_content),
            preprocessors=preprocessors or self._default_preprocessors,
        )

    def _upload_image(self, paranet_blob_name: str, image: PreprocessingImage) -> str:
        parent_path = path.dirname(paranet_blob_name)
        return self._file_storage.upload_content(
            path.join(parent_path, f"{uuid4().hex}.{image.extension}"),
            image.image_content,
            generate_unique_filename=False,
        )

    def _apply_transformations(self, document_id: int, preprocessed_images: list[tuple[str, str, PreprocessingImage]]) -> None:
        images = [
            PreprocessedImage(
                blob_name=blob_name,
                width=image.shape[0],
                height=image.shape[1],
                original_image_id=original_image_id,
            )
            for blob_name, original_image_id, image in preprocessed_images
        ]

        last_image: PreprocessingImage = preprocessed_images[0][-1]
        self._unifier.apply_transformations(document_id, images, last_image.applied_transformations.combine())

    def _revert_preprocessed_images(self, document_id: int, preprocessed_blobs: list[str]) -> None:
        self._event_publisher.publish(
            DOCUMENTS_AGGREGATE,
            str(document_id),
            [DeleteFiles(file_paths=preprocessed_blobs)],
            headers={"ID": uuid4().hex},
        )
