from typing import Any, Dict, Optional, Type, Union

from dependency_injector import containers, providers, resources
from deps_asb import ASBClient, ASBConsumer, ASBProducer
from deps_kafka import KafkaClient, KafkaConsumer, KafkaProducer
from deps_message_flow import MessagingDriverEnum
from deps_message_flow.events.publisher import DomainEventPublisher
from deps_message_flow.messaging.consumer import IMessageConsumer
from deps_message_flow.messaging.producer import IMessageProducer
from deps_rabbitmq import RabbitMQClient, RabbitMQConsumer, RabbitMQProducer

from deps_image_preprocess.application import ReferencePageService
from deps_image_preprocess.application.document_preprocessor.service import (
    DocumentPreprocessorService,
)
from deps_image_preprocess.constants import ASB_CUSTOM_SUBSCRIPTION_NAME
from deps_image_preprocess.domain.constants import ImagePreprocessorEnum
from deps_image_preprocess.domain.interfaces import (
    IImagePreprocessor,
    IImagePreprocessService,
)
from deps_image_preprocess.domain.services import ImagePreprocessService
from deps_image_preprocess.domain.services.preprocessors import (
    BlurringPreprocessor,
    GrayscalingPreprocessor,
    OrientationPreprocessor,
    RotationPreprocessor,
    ThresholdingPreprocessor,
)
from deps_image_preprocess.extras.storage import StorageControllerService
from deps_image_preprocess.infrastructure.services.proxies import UnifierProxy
from deps_image_preprocess.messaging.dispatcher import make_message_dispatcher

MessagingClient = Union[ASBClient, KafkaClient, RabbitMQClient]


class Core(containers.DeclarativeContainer):
    config = providers.Configuration()
    build_info: providers.Provider[Dict] = providers.Dict(
        {
            "build_tag": config.info.tag,
            "build_date": config.info.date,
            "commit_hash": config.info.hash,
        },
    )


class MessageBrokerResource(resources.Resource):
    def init(
        self,
        driver_type: str,
        expected_driver: str,
        client: Type[MessagingClient],
        message_connection_string: str,
        **kwargs: Dict[str, Any],
    ) -> Optional[MessagingClient]:
        return client(message_connection_string, **kwargs) if driver_type == expected_driver else None

    def shutdown(self, resource: Optional[MessagingClient]) -> None:
        if resource:
            resource.close()


class MessageBrokers(containers.DeclarativeContainer):
    config = providers.Configuration()
    messaging_driver_settings = providers.Dependency(instance_of=object)

    broker_client: providers.Provider[MessagingClient] = providers.Selector(
        config.messaging_driver,
        asb=providers.Resource(
            MessageBrokerResource,
            driver_type=MessagingDriverEnum.ASB.value,
            expected_driver=config.messaging_driver,
            client=ASBClient,
            message_connection_string=config.message_broker_connection_string,
            asb_settings=messaging_driver_settings,
        ),
        kafka=providers.Resource(
            MessageBrokerResource,
            driver_type=MessagingDriverEnum.KAFKA.value,
            expected_driver=config.messaging_driver,
            client=KafkaClient,
            message_connection_string=config.message_broker_connection_string,
            settings=messaging_driver_settings,
        ),
        rabbitmq=providers.Resource(
            MessageBrokerResource,
            driver_type=MessagingDriverEnum.RABBITMQ.value,
            expected_driver=config.messaging_driver,
            client=RabbitMQClient,
            message_connection_string=config.message_broker_connection_string,
            settings=messaging_driver_settings,
        ),
    )


class Messaging(containers.DeclarativeContainer):
    config = providers.Configuration()
    message_brokers = providers.DependenciesContainer()

    producer: providers.Provider[IMessageProducer] = providers.Selector(
        config.messaging_driver,
        asb=providers.Singleton(
            ASBProducer,
            client=message_brokers.broker_client,
            topic_name=config.messaging_driver_settings.topic_name,
        ),
        kafka=providers.Singleton(
            KafkaProducer,
            client=message_brokers.broker_client,
        ),
        rabbitmq=providers.Singleton(
            RabbitMQProducer,
            client=message_brokers.broker_client,
        ),
    )
    consumer: providers.Provider[IMessageConsumer] = providers.Selector(
        config.messaging_driver,
        asb=providers.Singleton(
            ASBConsumer,
            client=message_brokers.broker_client,
            topic_name=config.messaging_driver_settings.topic_name,
            custom_subscription_name=ASB_CUSTOM_SUBSCRIPTION_NAME,
        ),
        kafka=providers.Singleton(
            KafkaConsumer,
            client=message_brokers.broker_client,
        ),
        rabbitmq=providers.Singleton(
            RabbitMQConsumer,
            client=message_brokers.broker_client,
        ),
    )


class DomainEventPublishers(containers.DeclarativeContainer):
    messaging = providers.DependenciesContainer()

    publisher: providers.Singleton[DomainEventPublisher] = providers.Singleton(
        DomainEventPublisher,
        messaging.producer,
    )


class Preprocessors(containers.DeclarativeContainer):
    orientation_preprocessor: providers.Provider[OrientationPreprocessor] = providers.Singleton(OrientationPreprocessor)
    grayscaling_preprocessor: providers.Provider[GrayscalingPreprocessor] = providers.Singleton(GrayscalingPreprocessor)
    blurring_preprocessor: providers.Provider[IImagePreprocessor] = providers.Singleton(BlurringPreprocessor)
    thresholding_preprocessor: providers.Provider[ThresholdingPreprocessor] = providers.Singleton(
        ThresholdingPreprocessor,
        grayscaling_preprocessor,
    )
    rotation_preprocessor: providers.Provider[RotationPreprocessor] = providers.Singleton(
        RotationPreprocessor,
        blurring_preprocessor,
        thresholding_preprocessor,
    )


class Services(containers.DeclarativeContainer):
    config = providers.Configuration()
    domain_event_publishers = providers.DependenciesContainer()
    image_preprocessors: providers.Container[Preprocessors] = providers.Container(Preprocessors)
    image_preprocess_service: providers.Singleton[IImagePreprocessService] = providers.Singleton(
        ImagePreprocessService,
        available_preprocessors=providers.Dict(
            {
                ImagePreprocessorEnum.ORIENTATION: image_preprocessors.orientation_preprocessor,
                ImagePreprocessorEnum.GRAYSCALING: image_preprocessors.grayscaling_preprocessor,
                ImagePreprocessorEnum.BLURRING: image_preprocessors.blurring_preprocessor,
                ImagePreprocessorEnum.THRESHOLDING: image_preprocessors.thresholding_preprocessor,
                ImagePreprocessorEnum.ROTATION: image_preprocessors.rotation_preprocessor,
            }
        ),
        default_preprocessors=config.preprocess.default_preprocessors,
    )
    file_storage: providers.Provider[StorageControllerService] = providers.Singleton(
        StorageControllerService,
        config.file_storage_url,
    )
    unifier: providers.Provider[UnifierProxy] = providers.Singleton(
        UnifierProxy,
        config.unifier_url,
    )


class Application(containers.DeclarativeContainer):
    config = providers.Configuration()
    messaging_driver_settings = providers.Dependency(instance_of=object)

    core: providers.Container[Core] = providers.Container(Core, config=config)

    message_brokers: providers.Container[MessageBrokers] = providers.Container(
        MessageBrokers,
        config=config,
        messaging_driver_settings=messaging_driver_settings,
    )  # type: ignore
    messaging: providers.Container[Messaging] = providers.Container(  # type: ignore
        Messaging,
        config=config,
        message_brokers=message_brokers,
    )
    domain_event_publishers: providers.Container[DomainEventPublishers] = providers.Container(  # type: ignore
        DomainEventPublishers,
        messaging=messaging,
    )
    message_dispatcher: providers.Singleton[IMessageConsumer] = providers.Singleton(
        make_message_dispatcher,
        messaging.consumer,
        messaging.producer,
    )
    services: providers.Container[Services] = providers.Container(Services, config=config)
    reference_page_service: providers.Provider[ReferencePageService] = providers.Singleton(
        ReferencePageService,
        file_storage=services.file_storage,
        image_preprocess_service=services.image_preprocess_service,
        event_publisher=domain_event_publishers.publisher,
    )
    document_preprocessor_service: providers.Provider[DocumentPreprocessorService] = providers.Singleton(
        DocumentPreprocessorService,
        unifier_proxy=services.unifier,
        file_storage=services.file_storage,
        image_preprocess_service=services.image_preprocess_service,
        event_publisher=domain_event_publishers.publisher,
        default_preprocessors=config.preprocess.default_preprocessors,
    )
