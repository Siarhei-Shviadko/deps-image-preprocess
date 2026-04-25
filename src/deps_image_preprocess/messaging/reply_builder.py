from typing import Any
from uuid import uuid4

from deps_message_flow.commands.common import (
    CommandReplyOutcome,
    Failure,
    ReplyMessageHeaders,
    Success,
)
from deps_message_flow.events.mappers import JsonMapper
from deps_message_flow.messaging.common import IMessage
from deps_message_flow.messaging.producer import MessageBuilder

__all__ = [
    "ReplyBuilder",
]


class ReplyBuilder:
    @staticmethod
    def with_success(reply: Any = Success()) -> IMessage:
        return (
            MessageBuilder.with_payload(JsonMapper().serialize(reply))
            .with_header(ReplyMessageHeaders.REPLY_OUTCOME, CommandReplyOutcome.SUCCESS.value)
            .with_header(ReplyMessageHeaders.REPLY_TYPE, reply.__class__.__name__)
            .with_header(IMessage.ID, uuid4().hex)
            .build()
        )

    @staticmethod
    def with_failure(reply: Any = Failure()) -> IMessage:
        return (
            MessageBuilder.with_payload(JsonMapper().serialize(reply))
            .with_header(ReplyMessageHeaders.REPLY_OUTCOME, CommandReplyOutcome.FAILURE.value)
            .with_header(ReplyMessageHeaders.REPLY_TYPE, reply.__class__.__name__)
            .with_header(IMessage.ID, uuid4().hex)
            .build()
        )
