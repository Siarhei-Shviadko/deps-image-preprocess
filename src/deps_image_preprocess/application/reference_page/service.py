from imghdr import what
from io import BytesIO
from logging import getLogger
from os import path
from typing import Generator, Iterable
from uuid import uuid4

import numpy as np
import pypdfium2
from deps_message_flow.events.publisher import DomainEventPublisher

from deps_image_preprocess.constants import DOCUMENTS_AGGREGATE
from deps_image_preprocess.domain.constants import (
    ImageExtensionEnum,
    ImagePreprocessorEnum,
)
from deps_image_preprocess.domain.entities import PreprocessingImage
from deps_image_preprocess.domain.events import DeleteFiles
from deps_image_preprocess.domain.interfaces import IImagePreprocessService
from deps_image_preprocess.extras.storage import StorageControllerService

__all__ = [
    "ReferencePageService",
]


_logger = getLogger(__name__)

_DEFAULT_TARGET_DPI = 300
_PYPDFIUM2_ORIGINAL_DPI = 72


class _Blob:
    def __init__(self, blob_content: bytes, name: str):
        self._content = blob_content
        self._name = name

    @property
    def content(self) -> bytes:
        return self._content

    @property
    def extension(self) -> str:
        extension = path.splitext(self._name)[-1].split(".")[-1].lower()  # noqa: WPS221
        if extension:
            return extension

        extension = what(None, self._content)
        if extension:
            return extension

        return "unknown"


class _PDFObject(BytesIO):
    @property
    def pages_as_images(self) -> Iterable[PreprocessingImage]:
        pdf = pypdfium2.PdfDocument(self)
        for page_index, _ in enumerate(pdf):
            page = pdf.get_page(page_index)
            pil_image = page.render_topil(scale=_DEFAULT_TARGET_DPI / _PYPDFIUM2_ORIGINAL_DPI)
            yield PreprocessingImage(pixels=np.asarray(pil_image), extension=ImageExtensionEnum.PNG)


class ReferencePageService:
    IMAGE_SIZE_THRESHOLD = 1000 * 1000

    def __init__(
        self,
        file_storage: StorageControllerService,
        image_preprocess_service: IImagePreprocessService,
        event_publisher: DomainEventPublisher,
    ):
        self._file_storage = file_storage
        self._image_preprocess = image_preprocess_service
        self._event_publisher = event_publisher

    def preprocess(self, template_id: str, blob_names: list[str], path_to_save: str) -> list[str]:
        preprocessed_images = []
        try:
            for preprocess_image_path in self._preprocess_blobs(blob_names, path_to_save):
                preprocessed_images.append(preprocess_image_path)
        except Exception:
            _logger.warning("Error was caught, revert all saved images")
            if preprocessed_images:
                self._revert_preprocessed_images(template_id, preprocessed_images)
            raise

        return preprocessed_images

    def _preprocess_blobs(self, blob_names: list[str], path_to_save: str) -> Generator[str, None, None]:
        for blob_name in blob_names:
            _logger.info("Start preprocess reference pages for %s", blob_name)
            blob_content = self._file_storage.download_content(blob_name)
            yield from self._preprocess_blob(_Blob(blob_content, blob_name), path_to_save)

    def _preprocess_blob(self, blob: _Blob, path_to_save: str) -> Generator[str, None, None]:
        if blob.extension in list(ImageExtensionEnum):
            output_extension = (
                ImageExtensionEnum.PNG
                if ImageExtensionEnum(blob.extension) in {ImageExtensionEnum.TIFF, ImageExtensionEnum.TIF}
                else ImageExtensionEnum(blob.extension)
            )
            images = [PreprocessingImage.from_image_content(blob.content, extension=output_extension)]
        else:
            images = _PDFObject(blob.content).pages_as_images  # type: ignore

        for image in images:
            preprocessed_image = self._image_preprocess.execute(
                image=image,
                preprocessors=self._get_preprocessors_to_apply(image),
            )
            uploaded_path = self._file_storage.upload_content(
                path.join(path_to_save, f"{uuid4().hex}.{ImageExtensionEnum(preprocessed_image.extension).value}"),
                preprocessed_image.image_content,
                generate_unique_filename=False,
            )
            _logger.info("Reference page was successfully preprocessed: %s", uploaded_path)
            yield uploaded_path

    def _revert_preprocessed_images(self, template_id: str, preprocessed_images: list[str]) -> None:
        self._event_publisher.publish(
            DOCUMENTS_AGGREGATE,
            template_id,
            [DeleteFiles(file_paths=preprocessed_images)],
            headers={"ID": uuid4().hex},
        )

    def _get_preprocessors_to_apply(self, image: PreprocessingImage) -> list[ImagePreprocessorEnum]:
        preprocessors = list(ImagePreprocessorEnum)
        if image.shape[0] * image.shape[1] < self.IMAGE_SIZE_THRESHOLD:
            preprocessors.remove(ImagePreprocessorEnum.BLURRING)
        return preprocessors
