import logging
from typing import Optional

import requests  # type: ignore

from .adapter import DEPSHTTPSAdapter
from .api_key_auth import DEPSApiKeyAuth

__all__ = ["BaseRESTClient"]


class DepsAuthError(Exception):
    pass


class BaseRESTClient:
    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        access_token: Optional[str] = None,
    ) -> None:
        self._base_url = base_url

        self._api_key = api_key
        self._access_token = access_token

        self._logger = logging.getLogger(self.__class__.__name__)

        self._session = requests.Session()
        self._initialize()

    def _initialize(self) -> None:
        self._mount_adapter()
        self._set_session_headers()
        self._set_authentication()

    def _mount_adapter(self) -> None:
        self._session.mount(self._base_url, DEPSHTTPSAdapter())

    def _set_session_headers(self) -> None:
        pass

    def _set_authentication(self) -> None:
        if self._api_key:
            self._session.auth = DEPSApiKeyAuth(self._api_key)

        elif self._access_token:
            raise NotImplementedError("Authentication by an access token not implemented.")

        else:
            raise DepsAuthError("You should provide an api key or an access token.")
