import pytest

from deps_image_preprocess.domain.constants import ImagePreprocessorEnum
from deps_image_preprocess.domain.entities import PreprocessingImage
from deps_image_preprocess.domain.exceptions import ImagePreprocessServiceError
from deps_image_preprocess.domain.interfaces import IImagePreprocessor


class DummyPreprocessor(IImagePreprocessor):
    def __init__(self, name):
        self._name = name

    def apply(self, image: PreprocessingImage) -> PreprocessingImage:
        return self._save_transformation_to_image(image, name=self._name)


@pytest.fixture
def override_image_preprocessors_with_mock(preprocessors):
    orientation_preprocessor = preprocessors.orientation_preprocessor
    rotation_preprocessor = preprocessors.rotation_preprocessor
    grayscaling_preprocessor = preprocessors.grayscaling_preprocessor
    blurring_preprocessor = preprocessors.blurring_preprocessor
    thresholding_preprocessor = preprocessors.thresholding_preprocessor

    orientation_preprocessor.override(DummyPreprocessor("orientation"))
    rotation_preprocessor.override(DummyPreprocessor("rotation"))
    grayscaling_preprocessor.override(DummyPreprocessor("grayscaling"))
    blurring_preprocessor.override(DummyPreprocessor("blurring"))
    thresholding_preprocessor.override(DummyPreprocessor("thresholding"))

    yield

    orientation_preprocessor.reset_override()
    rotation_preprocessor.reset_override()
    grayscaling_preprocessor.reset_override()
    blurring_preprocessor.reset_override()
    thresholding_preprocessor.reset_override()


class TestImagePreprocessService:
    @pytest.mark.usefixtures("override_image_preprocessors_with_mock")
    @pytest.mark.parametrize("image", ["png_image", "jpg_image"])
    def test_apply_preprocessors__preprocessors_are_not_set__default_preprocessors_applied(
        self, preprocess_service, image, request, default_preprocessors
    ):
        processed = preprocess_service.execute(request.getfixturevalue(image))

        transformations = [transformation.name for transformation in processed.applied_transformations]
        assert transformations == default_preprocessors

    @pytest.mark.usefixtures("override_image_preprocessors_with_mock")
    @pytest.mark.parametrize("image", ["png_image", "jpg_image"])
    def test_apply_preprocessors__preprocessors_are_set__preprocessors_applied(
        self,
        preprocess_service,
        image,
        request,
    ):
        preprocessors = [ImagePreprocessorEnum.GRAYSCALING, ImagePreprocessorEnum.BLURRING]
        processed = preprocess_service.execute(request.getfixturevalue(image), preprocessors=preprocessors)

        transformations = [transformation.name for transformation in processed.applied_transformations]
        assert transformations == preprocessors

    @pytest.mark.usefixtures("override_image_preprocessors_with_mock")
    def test_apply_preprocessors__preprocessors_are_not_set__preprocessors_not_applied(self, preprocess_service, png_image):
        processed = preprocess_service.execute(png_image, preprocessors=[])

        assert not processed.applied_transformations

    def test_apply_preprocessors__preprocessor_is_not_available__error_raised(self, preprocess_service, png_image):
        preprocess_service._available_preprocessors = {}

        with pytest.raises(ImagePreprocessServiceError) as e:
            preprocess_service.execute(png_image)
