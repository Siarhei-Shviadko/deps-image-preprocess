from dataclasses import InitVar, dataclass, field
from typing import Any, Dict, List, Optional

AUTH_HEADER = "Authorization"
DEPS_TOKEN_HEADER = "deps-token"


@dataclass
class UserValueObject:
    subject: str
    groups: List[str]
    organisation: str
    _organisation: InitVar[str] = field(init=False, repr=False, default=None)
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    roles: List[str] = field(default_factory=list)
    token: Optional[str] = None
    deps_token: Optional[str] = None

    @property  # type: ignore
    def organisation(self):
        if self._organisation is None:
            return self.groups[0]
        return self._organisation

    @organisation.setter
    def organisation(self, value):
        if type(value) is property:
            # initial value not specified, use default
            value = UserValueObject._organisation
        self._organisation = value

    @classmethod
    def from_jwt(cls, decoded_token: Dict[str, Any]) -> "UserValueObject":
        return cls(  # type: ignore
            subject=decoded_token["sub"],
            roles=decoded_token["realm_access"]["roles"],
            groups=decoded_token["groups"],
            token=decoded_token["token"],
        )

    @classmethod
    def from_json(cls, decoded_token: Dict[str, Any]) -> "UserValueObject":
        return cls(
            subject=decoded_token["subject"],
            roles=decoded_token["roles"],
            groups=decoded_token["groups"],
            organisation=decoded_token["organisation"],
            email=decoded_token["email"],
            first_name=decoded_token["first_name"],
            last_name=decoded_token["last_name"],
            deps_token=decoded_token["deps_token"],
        )
