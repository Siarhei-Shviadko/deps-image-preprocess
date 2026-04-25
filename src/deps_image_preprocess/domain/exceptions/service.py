from .preprocess import ImagePreprocessException


class ServiceProxyError(ImagePreprocessException):
    code = "service_proxy_error"
