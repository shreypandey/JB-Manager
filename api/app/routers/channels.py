import logging
from fastapi import APIRouter, HTTPException
from ..crud import get_bot_and_channel_by_channel_id, update_channel

logger = logging.getLogger('jb-manager-api')
router = APIRouter(
    prefix="/channel",
)

@router.post("/{channel_id}/activate")
async def activate_channel(channel_id: str):
    bot, channel = await get_bot_and_channel_by_channel_id(channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    if str(channel.status) == "active":
        raise HTTPException(
            status_code=400,
            detail=f"Bot already active for the channel name: {channel.name}",
        )
    required_credentials = bot.required_credentials
    current_credentials = bot.credentials if bot.credentials else {}
    missing_credentials = [
        name for name in required_credentials if name not in current_credentials
    ]
    if missing_credentials:
        raise HTTPException(
            status_code=400,
            detail=f"Bot missing required credentials: {', '.join(missing_credentials)}",
        )
    channel_data = {}
    channel_data["status"] = "active"
    await update_channel(channel_id, channel_data)
    return {"status": "success"}


@router.get("/{channel_id}/deactivate")
async def deactivate_channel(channel_id: str):
    _, channel = await get_bot_and_channel_by_channel_id(channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    channel_data = {}
    channel_data["status"] = "inactive"
    await update_channel(channel_id, channel_data)
    return channel


@router.delete("/{channel_id}")
async def delete_channel(channel_id: str):
    _, channel = await get_bot_and_channel_by_channel_id(channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    channel_data = {}
    channel_data["status"] = "deleted"
    await update_channel(channel_id, channel_data)
    return {"status": "success"}