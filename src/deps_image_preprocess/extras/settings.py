from typing import Optional

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = ["AuthenticationSettings", "Settings", "ServiceInfoSettings"]


class AuthenticationSettings(BaseSettings):
    enabled: bool = Field(False, validation_alias="AUTH_ENABLED")
    verify_ssl: bool = Field(True, validation_alias="AUTH_VERIFY_SSL")
    certs_endpoint: Optional[str] = Field(None, validation_alias="AUTH_CERTS_ENDPOINT")
    encryption_algorithm: str = Field("RS256", validation_alias="AUTH_ENCRYPTION_ALGORITHM")
    api_key: Optional[str] = Field(None, validation_alias="API_KEY")

    @model_validator(mode="after")
    def validate_certs_endpoint_and_key(self) -> "AuthenticationSettings":
        if self.enabled and (self.certs_endpoint is None and self.api_key is None):
            raise ValueError(
                "Please provide OAUTH certificates endpoint via `AUTH_CERTS_ENDPOINT` " "or provide auth key via `API_KEY`",
            )
        return self


class ServiceInfoSettings(BaseSettings):
    tag: str = ""
    date: str = ""
    hash: str = ""

    model_config = SettingsConfigDict(env_prefix="SERVICE_INFO_")


class Settings(BaseSettings):
    info: ServiceInfoSettings = ServiceInfoSettings()
    auth: AuthenticationSettings = AuthenticationSettings()
    ocr_api_url: Optional[str] = Field(None, validation_alias="OCR_API_URL")
    file_storage_url: Optional[str] = Field(None, validation_alias="FILE_STORAGE_URL")
    tables_api_url: Optional[str] = Field(None, validation_alias="TABLES_API_URL")
    omr_service_url: Optional[str] = Field(None, validation_alias="OMR_SERVICE_URL")
    debug_mode: bool = Field(False, validation_alias="DEBUG_MODE")
