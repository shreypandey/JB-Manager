import json
import os
from pathlib import Path
import shutil
import subprocess
import logging
from typing import AsyncGenerator

from lib.data_models import (
    Flow,
    LanguageIntent,
    ChannelIntent,
    BotConfig,
    FlowIntent,
    Message,
    FSMOutput,
    FSMInput,
    MessageType,
    FSMIntent,
    UserInput,
    Callback,
    Channel,
    Language,
    Dialog,
    DialogMessage,
    DialogOption,
    BotIntent,
    RAG,
    RAGQuery,
    CallbackType,
)
from lib.models import JBSession
import crud
from extensions import producer

logger = logging.getLogger("flow")

kafka_broker = os.getenv("KAFKA_BROKER")
flow_topic = os.getenv("KAFKA_FLOW_TOPIC")
rag_topic = os.getenv("KAFKA_RAG_TOPIC")
language_topic = os.getenv("KAFKA_LANGUAGE_TOPIC")
channel_topic = os.getenv("KAFKA_CHANNEL_TOPIC")


def push_message(destination: str, flow_output: Flow | Language | Channel | RAG):
    if destination == "flow":
        producer.send_message(flow_topic, flow_output.model_dump_json())
    elif destination == "language":
        producer.send_message(language_topic, flow_output.model_dump_json())
    elif destination == "channel":
        producer.send_message(channel_topic, flow_output.model_dump_json())
    elif destination == "rag":
        producer.send_message(rag_topic, flow_output.model_dump_json())
    else:
        logger.error("Invalid destination: %s", destination)


async def handle_bot(bot_config: BotConfig):
    bot_id = bot_config.bot_id
    fsm_code = bot_config.bot.fsm_code
    requirements_txt = "openai\ncryptography\n" + bot_config.bot.requirements_txt
    index_urls = bot_config.bot.index_urls if bot_config.bot.index_urls else []

    bots_parent_directory = Path(__file__).parent
    bots_root_directory = Path(os.path.join(bots_parent_directory, "bots"))
    bot_dir = Path(os.path.join(bots_root_directory, bot_id))

    # remove directory if it already exists
    if bot_dir.exists():
        shutil.rmtree(bot_dir)
    if bot_config.intent == BotIntent.DELETE:
        logger.info("Deleted bot %s", bot_id)
        return
    elif bot_config.intent == BotIntent.INSTALL:
        bot_dir.mkdir(exist_ok=True, parents=True)

        # copy the contents of Path(__file__).parent/template into the bot's directory
        template_dir = Path(os.path.join(bots_parent_directory, "template"))
        for item in template_dir.iterdir():
            if item.is_dir():
                shutil.copytree(item, bot_dir / item.name)
            else:
                shutil.copy2(item, bot_dir)

        bot_code_file = Path(os.path.join(bot_dir, "bot.py"))
        bot_code_file.write_text(fsm_code)

        # create a requirements.txt file in the bot's directory
        requirements_file = Path(os.path.join(bot_dir, "requirements.txt"))
        requirements_file.write_text(requirements_txt)

        # create a venv inside the bot's directory
        venv_dir = Path(os.path.join(bot_dir, ".venv"))
        subprocess.run(["python3", "-m", "venv", venv_dir])
        install_command = [str(venv_dir / "bin" / "pip"), "install"]
        for index_url in index_urls:
            install_command.extend(["--extra-index-url", index_url])
        install_command.extend(["-r", requirements_file])
        subprocess.run(install_command)
        logger.info("Installed bot %s", bot_id)


async def manage_session(turn_id: str, new_session: bool = False) -> JBSession:
    if new_session:
        session = await crud.create_session(turn_id)
    else:
        session = await crud.get_session(turn_id)
    return session


async def handle_user_input(user_input: UserInput):
    turn_id = user_input.turn_id
    message = user_input.message
    message_type = message.message_type
    await crud.create_message(
        turn_id=turn_id,
        message_type=message_type.value,
        is_user_sent=True,
        message=getattr(message, message.message_type.value).model_dump_json(
            exclude_none=True
        ),
    )
    if message_type == MessageType.TEXT:
        # TODO: content filter
        fsm_input = FSMInput(user_input=message.text.body)
    elif message_type == MessageType.INTERACTIVE_REPLY:
        selected_options = json.dumps([
            option.model_dump(exclude_none=True)
            for option in message.interactive_reply.options
        ])
        fsm_input = FSMInput(user_input=selected_options)
    elif message_type == MessageType.FORM_REPLY:
        form_response = json.dumps(message.form_reply.form_data)
        fsm_input = FSMInput(user_input=form_response)
    else:
        return NotImplemented

    session = await manage_session(turn_id=turn_id)
    async for fsm_output in handle_fsm_input(fsm_input, session):
        await handle_fsm_output(turn_id, fsm_output)


async def handle_callback_input(callback: Callback):
    turn_id = callback.turn_id
    callback_type = callback.callback_type
    if callback_type == CallbackType.EXTERNAL:
        callback_input = callback.external
        fsm_input = FSMInput(callback_input=callback_input)
    elif callback_type == CallbackType.RAG:
        callback_input = [
            resp.model_dump_json(exclude_none=True) for resp in callback.rag_response
        ]
        callback_input = json.dumps(callback_input)
        fsm_input = FSMInput(callback_input=callback_input)
    session = await manage_session(turn_id=turn_id)
    async for fsm_output in handle_fsm_input(fsm_input, session):
        await handle_fsm_output(turn_id, fsm_output)


async def handle_dialog_input(dialog: Dialog):
    turn_id = dialog.turn_id
    dialog_id = dialog.message.dialog.dialog_id
    if dialog_id == DialogOption.CONVERSATION_RESET:
        fsm_input = FSMInput(user_input="reset")
        session = await manage_session(turn_id=turn_id, new_session=True)
    elif dialog_id == DialogOption.LANGUAGE_SELECTED:
        session = await manage_session(turn_id=turn_id)
        await crud.update_user_language(
            turn_id=turn_id, selected_language=dialog.message.dialog.dialog_input
        )
        fsm_input = FSMInput(user_input="language_selected")
    async for fsm_output in handle_fsm_input(fsm_input, session):
        await handle_fsm_output(turn_id, fsm_output)


async def handle_fsm_input(
    fsm_input: FSMInput, session: JBSession
) -> AsyncGenerator[FSMOutput, None]:
    bot_details = await crud.get_bot_by_id(session.bot_id)
    bot_id = bot_details.id
    bot_name = bot_details.name
    config_env = bot_details.config_env
    config_env = {} if config_env is None else config_env
    credentials = bot_details.credentials
    credentials = {} if credentials is None else credentials

    path = os.path.join(Path(__file__).parent, "bots", bot_id)

    ## need to pass state json and msg_text to the bot
    fsm_runner_input = {
        "fsm_input": fsm_input.model_dump(exclude_none=True),
        "state": session.variables,
        "bot_name": bot_name,
        "credentials": credentials,
        "config_env": config_env,
    }
    logger.error("fsm_runner_input: %s", json.dumps(fsm_runner_input))
    fsm_process = subprocess.run(
        [
            str(os.path.join(path, ".venv", "bin", "python")),
            str(os.path.join(path, "fsm_wrapper.py")),
            json.dumps(fsm_runner_input),
        ],
        capture_output=True,
        text=True,
    )

    if fsm_process.stderr:
        logger.error("Error while running fsm: %s", fsm_process.stderr)

    # logger.error("Output from fsm: %s", completed_process.stdout)
    for line in fsm_process.stdout.split("\n"):
        if not line:
            continue
        # logger.error("Output from fsm: %s", line)
        fsm_runner_output = json.loads(line)
        if "fsm_output" in fsm_runner_output:
            fsm_output = fsm_runner_output["fsm_output"]
            logger.info("Callback message: %s", fsm_output)
            # execute callback
            yield FSMOutput(**fsm_output)
        elif "new_state" in fsm_runner_output:
            # save new state to db
            new_state_variables = fsm_runner_output["new_state"]
            logger.info("FSM Runner message: %s", fsm_runner_output)
            await crud.update_session(session.id, new_state_variables)


async def handle_fsm_output(turn_id: str, fsm_output: FSMOutput):
    intent = fsm_output.intent
    if intent == FSMIntent.SEND_MESSAGE:
        message = fsm_output.message
        message_type = message.message_type
        if message_type == MessageType.FORM:
            destination = "channel"
            flow_output = Channel(
                source="flow",
                turn_id=turn_id,
                intent=ChannelIntent.CHANNEL_OUT,
                bot_output=message,
            )
        else:
            destination = "language"
            flow_output = Language(
                source="flow",
                turn_id=turn_id,
                intent=LanguageIntent.LANGUAGE_OUT,
                message=message,
            )
    elif intent == FSMIntent.CONVERSATION_RESET:
        destination = "flow"
        flow_output = Flow(
            source="flow",
            intent=FlowIntent.DIALOG,
            dialog=Dialog(
                turn_id=turn_id,
                message=Message(
                    message_type=MessageType.DIALOG,
                    dialog=DialogMessage(dialog_id=DialogOption.CONVERSATION_RESET),
                ),
            ),
        )
    elif intent == FSMIntent.LANGUAGE_CHANGE:
        destination = "channel"
        flow_output = Channel(
            source="flow",
            turn_id=turn_id,
            intent=ChannelIntent.CHANNEL_OUT,
            bot_output=Message(
                message_type=MessageType.DIALOG,
                dialog=DialogMessage(dialog_id=DialogOption.LANGUAGE_CHANGE),
            ),
        )
    elif intent == FSMIntent.RAG_CALL:
        destination = "rag"
        rag_query: RAGQuery = fsm_output.rag_query
        flow_output = RAG(
            source="flow",
            turn_id=turn_id,
            collection_name=rag_query.collection_name,
            query=rag_query.query,
            top_chunk_k_value=rag_query.top_chunk_k_value,
        )

    push_message(destination, flow_output)
