from . import ImagePreprocessException


class ImagePreprocessServiceError(ImagePreprocessException):
    code = "preprocess_service_error"


class PreprocessorError(ImagePreprocessException):
    code = "preprocessor_error"


class PreprocessingImageError(ImagePreprocessException):
    code = "preprocessing_image_error"
