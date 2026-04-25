from abc import ABC, abstractmethod

from deps_image_preprocess.domain.entities import Transformation
from deps_image_preprocess.domain.entities.preprocess import PreprocessingImage


class IImagePreprocessor(ABC):
    @abstractmethod
    def apply(self, image: PreprocessingImage) -> PreprocessingImage:
        pass

    @staticmethod
    def _save_transformation_to_image(image: PreprocessingImage, name: str, *args, **kwargs) -> PreprocessingImage:
        new_transformation = Transformation(name=name, args=list(args), kwargs=kwargs)
        image.applied_transformations.append(new_transformation)
        return image
