import logging

from dependency_injector.wiring import Provide, inject
from deps_message_flow.commands.common import make_message_for_command
from deps_message_flow.commands.consumer import CommandHandlerReplyBuilder
from deps_message_flow.commands.consumer.command_message import CommandMessage
from deps_message_flow.events.mappers import JsonMapper

from deps_image_preprocess.application import ReferencePageService
from deps_image_preprocess.containers import Application
from deps_image_preprocess.domain.constants import ImagePreprocessorEnum
from deps_image_preprocess.domain.events import (
    PerformPreprocessReply,
    PreprocessReferencePageReply,
)

from ..application.document_preprocessor.service import DocumentPreprocessorService
from .error_type import ErrorType
from .reply_builder import ReplyBuilder

logger = logging.getLogger(__name__)


__all__ = [
    "preprocess_reference_pages",
    "perform_preprocess",
]


@inject
def preprocess_reference_pages(
    command_message: CommandMessage,
    reference_page_service: ReferencePageService = Provide[Application.reference_page_service],
):
    template_id = command_message.command.template_id
    blob_names = command_message.command.blob_names

    try:
        preprocessed_images = reference_page_service.preprocess(
            template_id, blob_names, f"template/reference_page/{template_id}/"
        )
    except Exception as e:
        logger.error(f"Failed to preprocess reference pages! \n Reason: {e}")
        return [ReplyBuilder.with_failure(PreprocessReferencePageReply(template_id=template_id, blob_names=[]))]

    return [ReplyBuilder.with_success(PreprocessReferencePageReply(template_id=template_id, blob_names=preprocessed_images))]


@inject
def perform_preprocess(
    command_message: CommandMessage,
    document_preprocessor_service: DocumentPreprocessorService = Provide[Application.document_preprocessor_service],
):
    reply = PerformPreprocessReply(document_id=command_message.command.document_id)
    try:
        document_preprocessor_service.preprocess(
            document_id=command_message.command.document_id,
            preprocessors=[
                ImagePreprocessorEnum(transformation) for transformation in command_message.command.image_transformations
            ]
            if command_message.command.image_transformations
            else None,
        )

        return [ReplyBuilder.with_success(reply)]
    except Exception as e:
        logger.error(f"Failed to preprocess images for document `{command_message.command.document_id}` \n Reason: {e}")
        reply.error_type = ErrorType.SYSTEM
        reply.error_message = str(e)
        reply_command_message = make_message_for_command(
            channel="NONE",
            payload=JsonMapper().serialize(reply),
            command_type=reply.__class__.__name__,
            reply_to="NONE",
        )

        return [CommandHandlerReplyBuilder.with_success(reply_command_message)]
