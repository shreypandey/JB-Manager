import os
import logging
from typing import Dict

from fastapi import HTTPException
from lib.kafka_utils import KafkaProducer
from lib.channel_handler import ChannelHandler, PinnacleWhatsappHandler

logger = logging.getLogger('jb-manager-api')

channel_topic = os.getenv("KAFKA_CHANNEL_TOPIC")
flow_topic = os.getenv("KAFKA_FLOW_TOPIC")
if not channel_topic or not flow_topic:
    raise Exception("Kafka topics not set")


# Connect Kafka Producer automatically using env variables
# and SASL, if applicable
producer = KafkaProducer.from_env_vars()

def produce_message(message: str, topic: str):
    try:
        logger.info("Sending msg to %s topic: %s", topic, message)  # With this line
        producer.send_message(topic=topic, value=message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error producing message: {e}") from e

channel_map: Dict[str, type[ChannelHandler]] = {
    PinnacleWhatsappHandler.get_channel_name(): PinnacleWhatsappHandler,
}