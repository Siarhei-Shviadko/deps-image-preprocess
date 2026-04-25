import logging
from http import HTTPStatus
from json import JSONDecodeError

from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette import status
from starlette.requests import Request

from deps_image_preprocess.api.models import ErrorModel
from deps_image_preprocess.domain.exceptions import (
    AlreadyExistsError,
    ForbiddenError,
    ImagePreprocessException,
    NotFoundError,
)

logger = logging.getLogger(__name__)


def json_domain_error_handler(error: ImagePreprocessException, status_code: int):
    error_message = ErrorModel(code=error.code, message=str(error)).model_dump()
    return JSONResponse(status_code=status_code, content=error_message)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ImagePreprocessException)
    def handle_domain_exception(request: Request, error: ImagePreprocessException):  # noqa: WPS430
        mapper = [
            (ForbiddenError, HTTPStatus.FORBIDDEN),
            (NotFoundError, HTTPStatus.NOT_FOUND),
            (AlreadyExistsError, HTTPStatus.CONFLICT),
            (ImagePreprocessException, HTTPStatus.BAD_REQUEST),
        ]

        for error_type, status_code in mapper:
            if issubclass(type(error), error_type):
                return json_domain_error_handler(error, status_code)

    @app.exception_handler(JSONDecodeError)
    def json_decode_exception_handler(request: Request, exc: JSONDecodeError):  # noqa: WPS430
        message = str(jsonable_encoder(exc.msg))
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorModel(code="json_decode_error", message=message).model_dump(),
        )

    @app.exception_handler(ValidationError)
    def bad_request(request: Request, exc: ValidationError):  # noqa: WPS430
        return JSONResponse(
            status_code=HTTPStatus.BAD_REQUEST,
            content=ErrorModel(code="bad_request", message=str(exc)).model_dump(),
        )

    @app.exception_handler(Exception)
    def handle_all_errors(request: Request, error: Exception):  # noqa: WPS430
        logger.error(f"Unhandled error {error}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorModel(code="unhandled_error", message=str(error)).model_dump(),
        )
