import logging
from fastapi import APIRouter, HTTPException, Request
from lib.data_models import (
    FlowIntent,
    Flow,
    Bot,
    BotConfig,
    BotIntent,
)
from lib.models import JBBot
from lib.utils import EncryptionHandler
from ..schema import JBBotCode, JBChannelContent
from ..crud import create_bot, get_bot_list, get_bot_by_id, update_bot, create_channel, update_channel_by_bot_id, get_bot_and_channel_by_bot_identifier
from ..extensions import channel_map, flow_topic, produce_message

logger = logging.getLogger('jb-manager-api')
router = APIRouter(
    prefix="/bot",
)


@router.get("/")
async def get_bots():
    bots = await get_bot_list()
    return bots


@router.post("/install")
async def install_bot(install_content: JBBotCode):
    bot_data = install_content.model_dump()
    bot = await create_bot(bot_data)
    flow_input = Flow(
        source="api",
        intent=FlowIntent.BOT,
        bot_config=BotConfig(
            bot_id=bot.id,
            intent=BotIntent.INSTALL,
            bot=Bot(
                name=bot.name,
                fsm_code=bot.code,
                requirements_txt=bot.requirements,
                index_urls=bot.index_urls,
            ),
        ),
    )
    produce_message(flow_input.model_dump_json(), topic=flow_topic)
    return {"status": "success"}


@router.delete("/{bot_id}")
async def delete_bot(bot_id: str):
    bot = await get_bot_by_id(bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    bot_data = {"status": "deleted"}
    await update_bot(bot_id, bot_data)
    await update_channel_by_bot_id(bot_id, bot_data)
    return {"status": "success"}


@router.post("/{bot_id}/add_channel")
async def add_channel(bot_id: str, channel_content: JBChannelContent):
    if channel_content.name not in channel_map:
        raise HTTPException(
            status_code=400, detail="Channel not supported by this manager"
        )
    bot: JBBot = await get_bot_by_id(bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    bot, channel = await get_bot_and_channel_by_bot_identifier(
        bot_identifier=channel_content.app_id, channel=channel_content.name
    )
    print(bot, channel)
    if channel:
        raise HTTPException(
            status_code=400,
            detail=f"App ID {channel_content.app_id} already in use by bot {bot.name}",
        )

    channel_content.key = EncryptionHandler.encrypt_text(channel_content.key)
    await create_channel(bot_id, channel_content)
    return {"status": "success"}


@router.post("/bot/{bot_id}/configure")
async def add_bot_configuraton(bot_id: str, request: Request):
    request_body = await request.json()
    bot: JBBot = await get_bot_by_id(bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    credentials = request_body.get("credentials")
    config_env = request_body.get("config_env")
    if credentials is None and config_env is None:
        raise HTTPException(
            status_code=400, detail="No credentials or config_env provided"
        )
    bot_data = {}
    if credentials is not None:
        encrypted_credentials = EncryptionHandler.encrypt_dict(credentials)
        bot_data["credentials"] = encrypted_credentials
    if config_env is not None:
        bot_data["config_env"] = config_env
    await update_bot(bot_id, bot_data)
    return {"status": "success"}
