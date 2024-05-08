import os
import asyncio
import json
import traceback
import logging
from dotenv import load_dotenv


from lib.data_models import (
    Flow,
    BotConfig,
    FlowIntent,
    Bot,
    BotIntent,
)
from handlers import (
    handle_callback_input,
    handle_dialog_input,
    handle_user_input,
    handle_bot,
)
from extensions import consumer
import crud

load_dotenv()

logger = logging.getLogger("flow")
logger.info("Starting Listening")

kafka_broker = os.getenv("KAFKA_BROKER")
flow_topic = os.getenv("KAFKA_FLOW_TOPIC")
rag_topic = os.getenv("KAFKA_RAG_TOPIC")
language_topic = os.getenv("KAFKA_LANGUAGE_TOPIC")
channel_topic = os.getenv("KAFKA_CHANNEL_TOPIC")


async def flow_init():
    # install()
    # fetch all bots from db and install them
    bots = await crud.get_all_bots()
    for bot in bots:
        try:
            bot_config = BotConfig(
                bot_id=bot.id,
                intent=BotIntent.INSTALL,
                bot=Bot(
                    name=bot.name,
                    fsm_code=bot.code,
                    requirements_txt=bot.requirements,
                    index_urls=bot.index_urls,
                ),
            )
            await handle_bot(bot_config)
        except Exception as e:
            logger.error(
                "Error while installing bot: %s :: %s", e, traceback.format_exc()
            )


async def handle_flow_input(flow_input: Flow):
    flow_intent = flow_input.intent
    if flow_intent == FlowIntent.BOT:
        await handle_bot(flow_input.bot_config)
    elif flow_intent == FlowIntent.DIALOG:
        await handle_dialog_input(flow_input.dialog)
    elif flow_intent == FlowIntent.CALLBACK:
        await handle_callback_input(flow_input.callback)
    elif flow_intent == FlowIntent.USER_INPUT:
        await handle_user_input(flow_input.user_input)
    else:
        logger.error("Invalid flow intent: %s", flow_intent)


async def flow_loop():
    logger.info("Installing bots")
    try:
        await flow_init()
    except Exception as e:
        logger.error("Error while installing bots: %s :: %s", e, traceback.format_exc())
    logger.info("Finished installing bots, starting flow loop")

    while True:
        try:
            logger.info("Waiting for message")
            msg = consumer.receive_message(flow_topic)
            msg = json.loads(msg)
            logger.info("Message Recieved :: %s", msg)
            flow_input = Flow(**msg)
            await handle_flow_input(flow_input)
        except Exception as e:
            logger.error("Error in flow loop: %s :: %s", e, traceback.format_exc())


if __name__ == "__main__":
    asyncio.run(flow_loop())
