import json
from contextvars import ContextVar
from typing import Dict

import requests  # type: ignore

__all__ = ["DEPSTokenAuth"]


class DEPSTokenAuth(requests.auth.AuthBase):
    DEPS_TOKEN_HEADER = "deps-token"  # noqa: S105

    def __init__(self, user_context: ContextVar):
        self._user_context = user_context

    def __call__(self, request: requests.PreparedRequest) -> requests.PreparedRequest:
        request.headers.update(self._make_deps_token_header())

        return request

    def _make_deps_token_header(self) -> Dict[str, str]:
        return {self.DEPS_TOKEN_HEADER: json.dumps(self._user_context.get(None))}
