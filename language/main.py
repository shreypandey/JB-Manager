"""Main module for language service."""
import asyncio
import json
import os
import logging
import traceback
from typing import List

from crud import get_user_preferred_language
from dotenv import load_dotenv
from handlers import handle_input, handle_output

from lib.data_models import Language as LanguageInput
from lib.data_models import LanguageIntent, Flow, FlowIntent, UserInput, Message, Channel, ChannelIntent
from lib.kafka_utils import KafkaConsumer, KafkaProducer
from lib.model import Language

load_dotenv()

logger = logging.getLogger("language")
logger.setLevel(logging.INFO)

kafka_broker = os.getenv("KAFKA_BROKER")
flow_topic = os.getenv("KAFKA_FLOW_TOPIC")
language_topic = os.getenv("KAFKA_LANGUAGE_TOPIC")
channel_topic = os.getenv("KAFKA_CHANNEL_TOPIC")

logger.info("Connecting with topic: %s", language_topic)

consumer = KafkaConsumer.from_env_vars(
    group_id="cooler_group_id", auto_offset_reset="latest"
)
producer = KafkaProducer.from_env_vars()

logger.info("Connected with topic: %s", language_topic)


def send_message(data: Flow | Channel):
    """Sends message to Kafka topic"""
    topic = flow_topic if isinstance(data, Flow) else channel_topic
    msg = data.model_dump_json(exclude_none=True)
    logger.info("Sending message to %s topic: %s", topic, msg)
    producer.send_message(topic, msg)


async def handle_message(language_input: LanguageInput):
    """Handler for Language Input"""
    turn_id = language_input.turn_id
    message = language_input.message
    message_intent = language_input.intent

    preferred_language_code = await get_user_preferred_language(turn_id)
    if preferred_language_code is None:
        preferred_language = Language.EN
    else:
        preferred_language = Language.__members__.get(preferred_language_code.upper(), Language.EN)
    logger.info("User Preferred Language: %s", preferred_language)

    if message_intent == LanguageIntent.LANGUAGE_IN:
        message = await handle_input(
            preferred_language=preferred_language,
            message=message,
        )
        flow_input = Flow(
            source="language",
            intent=FlowIntent.USER_INPUT,
            user_input=UserInput(
                turn_id=turn_id,
                message=message,
            )
        )
        send_message(flow_input)
    elif message_intent == LanguageIntent.LANGUAGE_OUT:
        turn_id = language_input.turn_id
        messages: List[Message] = await handle_output(
            preferred_language=preferred_language,
            message=message,
        )
        logger.info("Messages %s", len(messages))
        for message in messages:
            channel_input = Channel(
                source="language",
                turn_id=turn_id,
                intent=ChannelIntent.CHANNEL_OUT,
                bot_output=message,
            )
            send_message(channel_input)


async def start():
    """Starts the language service."""
    while True:
        try:
            msg = consumer.receive_message(language_topic)
            logger.info("Received message %s", msg)
            msg = json.loads(msg)
            input_data = LanguageInput(**msg)
            logger.info("Received message %s", input_data)
            await handle_message(input_data)
        except Exception as e:
            logger.error("Error %s :: %s", e, traceback.format_exc())


asyncio.run(start())
