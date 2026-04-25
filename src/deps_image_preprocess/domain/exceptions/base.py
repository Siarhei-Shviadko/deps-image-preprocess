class ImagePreprocessException(Exception):
    code = "image_preprocess_exception"


class NotFoundError(ImagePreprocessException):
    code = "not_found_error"


class AlreadyExistsError(ImagePreprocessException):
    code = "already_exists_error"


class ForbiddenError(ImagePreprocessException):
    code = "forbidden_error"
