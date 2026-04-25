import contextvars

from deps_image_preprocess.extras.value_objects import UserValueObject

user: contextvars.ContextVar[UserValueObject] = contextvars.ContextVar("user")
