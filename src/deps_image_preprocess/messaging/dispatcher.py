import logging

from deps_message_flow.commands.consumer import (
    CommandDispatcher,
    CommandHandlersBuilder,
)
from deps_message_flow.messaging.consumer import IMessageConsumer
from deps_message_flow.messaging.producer import IMessageProducer

from deps_image_preprocess.constants import COMMANDS_QUEUE, IMAGE_PREPROCESS_COMMANDS
from deps_image_preprocess.domain.events import (
    PerformPreprocess,
    PreprocessReferencePage,
)

logger = logging.getLogger(__name__)


def make_message_dispatcher(subscriber: IMessageConsumer, producer: IMessageProducer) -> IMessageConsumer:
    from deps_image_preprocess.messaging.handlers import (  # noqa: WPS433
        perform_preprocess,
        preprocess_reference_pages,
    )

    commands_handlers = (
        CommandHandlersBuilder.from_channel(IMAGE_PREPROCESS_COMMANDS)
        .on_message(PreprocessReferencePage, preprocess_reference_pages)
        .on_message(PerformPreprocess, perform_preprocess)
        .for_queue(COMMANDS_QUEUE)
        .build()
    )

    cd = CommandDispatcher(commands_handlers, subscriber, producer)
    cd.initialize()

    logger.info("Start consuming...")

    return subscriber
