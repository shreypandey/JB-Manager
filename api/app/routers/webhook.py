import logging
from fastapi import APIRouter, HTTPException, Request
from lib.data_models import (
    FlowIntent,
    Flow,
    Callback
)
from ..extensions import flow_topic
from ..crud import get_plugin_reference

logger = logging.getLogger('jb-manager-api')
router = APIRouter()

def extract_reference_id(text):
    JB_IDENTIFIER = "jbkey"
    if JB_IDENTIFIER not in text:
        return None
    start_index = text.find(JB_IDENTIFIER)
    if start_index == -1:
        return None  # Start magic string not found

    new_index = start_index + len(JB_IDENTIFIER)
    end_index = text.find(JB_IDENTIFIER, new_index)
    if end_index == -1:
        return None  # End magic string not found

    return text[start_index : end_index + len(JB_IDENTIFIER)]

@router.post("/webhook")
async def plugin_webhook(request: Request):
    webhook_data = await request.body()
    webhook_data = webhook_data.decode("utf-8")
    plugin_uuid = extract_reference_id(webhook_data)
    if not plugin_uuid:
        raise HTTPException(
            status_code=400, detail="Plugin UUID not found in webhook data"
        )
    logger.info("Plugin UUID: %s", plugin_uuid)
    plugin_reference = await get_plugin_reference(plugin_uuid)
    logger.info("Webhook Data: %s", webhook_data)
    turn_id: str = plugin_reference.turn_id
    flow_input = Flow(
        source="api",
        intent=FlowIntent.CALLBACK,
        callback=Callback(
            turn_id=turn_id,
            callback_input=webhook_data,
        ),
    )
    produce_message(flow_input.model_dump_json(), topic=flow_topic)
    return 200
