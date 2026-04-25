import pytest

from deps_image_preprocess.domain.constants import ImageExtensionEnum
from tests.factories.preprocess import (
    PreprocessingImageFactory,
    get_pixel_array_from_file,
)


class TestImagePreprocessService:
    path = "tests/data/"

    @pytest.mark.parametrize("image_path", ["image_0.png", "image_27.png"])
    def test_execute__png_images__preprocessed(self, preprocess_service, image_path, default_preprocessors):
        pixels = get_pixel_array_from_file(f"{self.path}{image_path}")
        image = PreprocessingImageFactory(pixels=pixels, extension=ImageExtensionEnum.PNG)
        processed = preprocess_service.execute(image)

        transformations = [transformation.name for transformation in processed.applied_transformations]
        assert transformations == default_preprocessors

    @pytest.mark.parametrize("image_path", ["image_180.jpg", "image_270.jpg"])
    def test_execute__jpg_images__preprocessed(self, preprocess_service, image_path, default_preprocessors):
        pixels = get_pixel_array_from_file(f"{self.path}{image_path}")
        image = PreprocessingImageFactory(pixels=pixels, extension=ImageExtensionEnum.JPG)
        processed = preprocess_service.execute(image)

        transformations = [transformation.name for transformation in processed.applied_transformations]
        assert transformations == default_preprocessors
