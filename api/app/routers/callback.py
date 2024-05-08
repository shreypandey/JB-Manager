import logging
from typing import Optional
from fastapi import APIRouter, Request
from lib.data_models import (
    Channel,
    ChannelIntent,
    RestBotInput,
)
from lib.channel_handler import ChannelHandler
from ..crud import (
    get_bot_and_channel_by_bot_identifier,
    create_user,
    get_user_by_identifier,
    create_turn,
)
from ..extensions import channel_map, channel_topic, produce_message


logger = logging.getLogger("jb-manager-api")
router = APIRouter()


async def handle_callback(
    data: dict, headers: dict, query_params: dict, chosen_channel: type[ChannelHandler]
):
    processed_response = []
    for channel_data in chosen_channel.process_message(data):
        bot_identifier = channel_data.bot_identifier
        user = channel_data.user
        message_data = channel_data.message_data

        jb_bot, jb_channel = await get_bot_and_channel_by_bot_identifier(
            bot_identifier, chosen_channel.get_channel_name()
        )
        if jb_bot is None:
            err = ValueError(f"Active Bot not found for identifier: {bot_identifier}")
            logger.error(err)
            processed_response.append((err, None))

        bot_id: str = jb_bot.id
        jb_user = await get_user_by_identifier(user.user_identifier, bot_id)

        if jb_user is None:
            # register user
            logger.info("Registering user")
            jb_user = await create_user(
                bot_id, user.user_identifier, user.user_name, user.user_name
            )

        turn_id = await create_turn(
            bot_id=bot_id,
            channel_id=jb_channel.id,
            user_id=jb_user.id
        )

        channel_input = Channel(
            source="api",
            turn_id=turn_id,
            intent=ChannelIntent.CHANNEL_IN,
            bot_input=RestBotInput(
                channel_name=chosen_channel.get_channel_name(),
                headers=headers,
                data=message_data,
                query_params=query_params,
            ),
        )
        processed_response.append((None, channel_input))
    return processed_response


@router.post("/callback")
async def callback(request: Request):
    data = await request.json()
    headers = dict(request.headers)
    query_params = dict(request.query_params)
    chosen_channel: Optional[type[ChannelHandler]] = None
    for channel in channel_map.values():
        if channel.is_valid_data(data):
            chosen_channel = channel
            break
    if chosen_channel is None:
        logger.error("No valid channel found")
        return 404

    processed_callbacks = await handle_callback(
        data, headers, query_params, chosen_channel
    )
    for err, channel_input in processed_callbacks:
        if err:
            logger.error("Error processing message: %s", err)
            continue
        # write to channel
        produce_message(
            channel_input.model_dump_json(exclude_none=True), topic=channel_topic
        )

    return 200
