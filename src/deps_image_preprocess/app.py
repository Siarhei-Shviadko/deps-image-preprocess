import logging
import os

import uvicorn
from fastapi import FastAPI
from fastapi.routing import APIRoute

from deps_image_preprocess import api, constants
from deps_image_preprocess.containers import Application
from deps_image_preprocess.error_handlers import register_error_handlers
from deps_image_preprocess.extras.fastapi_utils import add_auth_to_openapi
from deps_image_preprocess.infrastructure.access_management import user
from deps_image_preprocess.messaging import handlers
from deps_image_preprocess.settings import Settings

logger = logging.getLogger(__name__)


def init_application(settings: Settings) -> Application:
    settings = Settings()
    app = Application(messaging_driver_settings=settings.messaging_driver_settings)
    app.config.from_dict(settings.model_dump())
    app.init_resources()

    if app.config.authentication.enabled():
        app.services.file_storage().set_user_context(user)
        app.message_brokers.broker_client().user_context = user

    app.services.wire(packages=(api,))
    app.core.wire(packages=(api,))
    app.wire(packages=(handlers,))

    return app


def create_fastapi() -> FastAPI:
    settings = Settings()
    app: Application = init_application(settings)
    _base_service_init(app)

    fastapi_app = FastAPI(
        title=constants.PROJECT_NAME,
        version=app.config.version(),
        docs_url=f"{constants.API_PREFIX}{constants.SWAGGER_DOC_URL}",
        description=constants.DESCRIPTION,
        openapi_url=f"{constants.API_PREFIX}/openapi.json",
    )
    fastapi_app.include_router(api.router, prefix=constants.BASE_API_PREFIX)
    fastapi_app.app = app

    register_error_handlers(fastapi_app)
    register_auth(fastapi_app)
    use_route_names_as_operation_ids(fastapi_app)

    if app.config.instrumentation_enabled():
        from deps_observability_instrumentation import (  # noqa: WPS433
            instrument_fast_api,
        )

        instrument_fast_api(fastapi_app)

    return fastapi_app


def register_auth(app: FastAPI):
    add_auth_to_openapi(app)


def use_route_names_as_operation_ids(app: FastAPI) -> None:
    for route in app.routes:
        if isinstance(route, APIRoute):
            route.operation_id = route.name


def run_api():
    env = os.getenv("ENV", "prod")
    options = {
        "host": "0.0.0.0",  # noqa: S104
        "port": 8000,
        "log_level": os.getenv("LOG_LEVEL", "debug").lower(),
        "reload": env == "development",
        "debug": env == "development",
    }

    uvicorn.run("deps_image_preprocess.app:create_fastapi", **options)


def run_message_dispatcher() -> None:
    settings = Settings()
    app: Application = init_application(settings)
    _base_service_init(app)

    dispatcher = app.message_dispatcher()
    dispatcher.start_consuming()


def _base_service_init(app: Application) -> None:
    if app.config.instrumentation_enabled():
        logger.info("Instrumentation enabled.")
        from deps_observability_instrumentation import (  # noqa: WPS433
            instrument_messaging,
            setup_instrumentation,
        )

        setup_instrumentation()
        instrument_messaging(app.messaging.producer(), app.messaging.consumer())
