from contextvars import ContextVar
from typing import Dict, Optional

from requests import Session

AUTH_HEADER = "Authorization"
DEPS_TOKEN_HEADER = "deps-token"
JWT_PREFIX = "Bearer "
KEY_PREFIX = "Key "


class DepsAuthError(Exception):
    pass


class AuthDriverMixin:
    def __init__(
        self,
        api_key: Optional[str] = None,
        access_token: Optional[str] = None,
    ):
        self.__session = Session()

        self._api_key = api_key
        self._access_token = access_token
        self._user_context: Optional[ContextVar] = None

    def set_user_context(self, user_context: ContextVar) -> None:
        self._user_context = user_context

    @property
    def _session(self) -> Session:
        headers = self._get_auth_header()
        if headers:
            self._set_auth_headers(headers)
        return self.__session

    @_session.setter
    def _session(self, session: Session) -> None:
        self.__session = session

    def _get_auth_header(self) -> Optional[Dict[str, str]]:
        # If any token is provided, trying to auth
        user_context = self._get_user_context()
        if any((self._api_key, self._access_token, self._user_context)):
            if user_context and (user_context.get("token") or user_context.get("deps_token")):
                return self._create_tokens_from_user_context(user_context)
            tokens_priority = [
                (AUTH_HEADER, KEY_PREFIX, self._api_key),
                (AUTH_HEADER, JWT_PREFIX, self._access_token),
            ]
            for header, prefix, token_candidate in tokens_priority:
                if token_candidate:
                    return self._create_auth_token_header(header, prefix, token_candidate)
            raise DepsAuthError("Authorization token of current user is empty")
        return None

    def _create_tokens_from_user_context(self, user_context) -> Dict[str, str]:
        tokens = {}
        if user_context.get("deps_token") is not None:
            empty_prefix = ""
            tokens.update(self._create_auth_token_header(DEPS_TOKEN_HEADER, empty_prefix, user_context["deps_token"]))
        if user_context.get("token") is not None:
            tokens.update(self._create_auth_token_header(AUTH_HEADER, JWT_PREFIX, user_context["token"]))
        return tokens

    def _get_user_context(self) -> ContextVar:
        return self._user_context.get() if self._user_context and self._user_context.get(None) else None

    def _set_auth_headers(self, headers: Dict[str, str]) -> None:
        self.__session.headers.update(headers)

    @staticmethod
    def _create_auth_token_header(header: str, prefix: str, token: str) -> Dict[str, str]:
        return {header: f"{prefix}{token}"}
