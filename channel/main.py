import asyncio
import json
import logging
import os
import traceback
from typing import Dict

from dotenv import load_dotenv

from lib.kafka_utils import KafkaConsumer, KafkaProducer
from lib.data_models import (
    Channel,
    ChannelIntent,
    Message,
    BotInput,
    MessageType,
    Language,
    LanguageIntent,
    Flow,
    FlowIntent,
    Dialog,
    UserInput
)
from lib.channel_handler import ChannelHandler, PinnacleWhatsappHandler
from crud import (
    create_message,
    get_channel_by_turn_id,
    get_user_by_turn_id,
)

load_dotenv()

logging.basicConfig()
logger = logging.getLogger("channel")
logger.setLevel(logging.INFO)

channel_topic = os.getenv("KAFKA_CHANNEL_TOPIC")
language_topic = os.getenv("KAFKA_LANGUAGE_TOPIC")
flow_topic = os.getenv("KAFKA_FLOW_TOPIC")

logger.info("Connecting to kafka topic: %s", channel_topic)
consumer = KafkaConsumer.from_env_vars(
    group_id="cooler_group_id", auto_offset_reset="latest"
)
logger.info("Connected to kafka topic: %s", channel_topic)

logger.info("Connecting to kafka topic: %s", language_topic)
producer = KafkaProducer.from_env_vars()
logger.info("Connected to kafka topic: %s %s", language_topic, flow_topic)

channel_map: Dict[str, type[ChannelHandler]] = {
    PinnacleWhatsappHandler.get_channel_name(): PinnacleWhatsappHandler,
}


async def process_incoming_messages(channel_input: Channel):
    """Process incoming messages"""
    turn_id = channel_input.turn_id
    bot_input: BotInput = channel_input.bot_input
    channel = channel_map[bot_input.channel_name]

    jb_channel = await get_channel_by_turn_id(turn_id)
    message: Message = channel.to_message(
        turn_id=turn_id, channel=jb_channel, bot_input=bot_input
    )

    logger.info("Got a message: %s", message)
    if message:
        message_type = message.message_type
        logger.info("Message data: %s", message)
        logger.info("Message type: %s", message_type)
        if (
            message_type == MessageType.TEXT
            or message_type == MessageType.AUDIO
            or message_type == MessageType.IMAGE
            or message_type == MessageType.DOCUMENT
        ):
            language_input = Language(
                source="channel",
                turn_id=turn_id,
                intent=LanguageIntent.LANGUAGE_IN,
                message=message,
            )
            producer.send_message(
                language_topic, language_input.model_dump_json(exclude_none=True)
            )
        else:
            if message_type == MessageType.DIALOG:
                flow_input = Flow(
                    source="channel",
                    intent=FlowIntent.DIALOG,
                    dialog=Dialog(
                        turn_id=turn_id,
                        message=message
                    ),
                )
            else:
                flow_input = Flow(
                    source="channel",
                    intent=FlowIntent.USER_INPUT,
                    user_input=UserInput(
                        turn_id=turn_id,
                        message=message
                    ),
                )
            producer.send_message(
                flow_topic, flow_input.model_dump_json(exclude_none=True)
            )


async def send_message_to_user(message: Channel):
    """Send Message to user"""
    turn_id = message.turn_id
    message: Message = message.bot_output
    jb_user = await get_user_by_turn_id(turn_id=turn_id)
    jb_channel = await get_channel_by_turn_id(turn_id)
    channel_handler = channel_map[jb_channel.name]
    channel_handler.send_message(channel=jb_channel, user=jb_user, message=message)

    logger.info("Message type: %s", message.message_type)
    await create_message(
        turn_id=turn_id,
        message_type=message.message_type.value,
        is_user_sent=False,
        message=getattr(message, message.message_type.value).model_dump_json(
            exclude_none=True
        ),
    )
    logger.info("Message sent")


async def start_channel():
    """Starts the channel server"""
    logger.info("Starting Listening")
    while True:
        try:
            msg = consumer.receive_message(channel_topic)
            msg = json.loads(msg)
            logger.info("Input received: %s", msg)
            input_data = Channel(**msg)
            logger.info("Input received in object form: %s", input_data)
            if input_data.intent == ChannelIntent.CHANNEL_IN:
                await process_incoming_messages(input_data)
            elif input_data.intent == ChannelIntent.CHANNEL_OUT:
                await send_message_to_user(input_data)
        except Exception as e:
            logger.error("Error %s", e)
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(start_channel())
