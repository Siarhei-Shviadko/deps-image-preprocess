from typing import Any, Optional

from deps_asb import ASBSettings
from deps_kafka import KafkaSettings
from deps_message_flow import MessagingDriverEnum
from deps_rabbitmq import RabbitMQTLSSettings
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from deps_image_preprocess.domain.constants import ImagePreprocessorEnum
from deps_image_preprocess.extras.settings import (
    AuthenticationSettings,
    ServiceInfoSettings,
)


class PreprocessSettings(BaseSettings):
    default_preprocessors: list[ImagePreprocessorEnum] = Field(
        list(ImagePreprocessorEnum), validation_alias="DEFAULT_PREPROCESSORS"
    )


class Settings(BaseSettings):
    env: str = "local"
    version: str = "1.0"
    logger_level: str = Field("INFO", validation_alias="LOG_LEVEL")

    info: ServiceInfoSettings = ServiceInfoSettings()
    authentication: AuthenticationSettings = AuthenticationSettings()

    preprocess: PreprocessSettings = PreprocessSettings()

    file_storage_url: str
    unifier_url: str

    messaging_driver: MessagingDriverEnum = Field(MessagingDriverEnum.RABBITMQ, validation_alias="MESSAGING_DRIVER")
    messaging_driver_settings: Optional[Any] = Field(None, validation_alias="MESSAGING_DRIVER_SETTINGS")
    message_broker_connection_string: str

    instrumentation_enabled: bool = False

    model_config = SettingsConfigDict(use_enum_values=True)

    @classmethod
    @field_validator("messaging_driver_settings")
    def validate_messaging_driver_settings(cls, v, info):  # noqa: N805, WPS110
        messaging_driver = info.data.get("messaging_driver")
        if not messaging_driver:
            raise ValueError("Invalid messaging driver")

        driver = MessagingDriverEnum(messaging_driver)
        if driver == MessagingDriverEnum.ASB:
            return ASBSettings()
        elif driver == MessagingDriverEnum.KAFKA:
            return KafkaSettings()
        elif driver == MessagingDriverEnum.RABBITMQ:
            return RabbitMQTLSSettings().model_dump()  # TODO: use BaseSettings

        raise ValueError(f"Driver {driver} is not implemented")
