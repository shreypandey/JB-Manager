"""
Handlers for Language Input and Output
"""

import logging
import uuid
from lib.audio_converter import convert_to_wav_with_ffmpeg
from lib.data_models import (
    MessageType,
    Message,
    TextMessage,
    AudioMessage,
    ListMessage,
    ButtonMessage,
    DocumentMessage,
    ImageMessage,
)
from lib.model import Language
from extension import speech_processor, storage, translator


logger = logging.getLogger("language")
logger.setLevel(logging.INFO)


async def handle_input(preferred_language: Language, message: Message) -> Message:
    """Handler for Language Input"""
    message_type = message.message_type
    if message_type == MessageType.TEXT:
        message_text = message.text.body
        logger.info(
            "Received %s text message %s", preferred_language.name, message_text
        )
        vernacular_text = message_text
        english_text = await translator.translate_text(
            vernacular_text,
            preferred_language,
            Language.EN,
        )
        logger.info("English Text %s", english_text)
    elif message_type == MessageType.AUDIO:
        audio_url = message.audio.media_url
        wav_data = await convert_to_wav_with_ffmpeg(audio_url)
        vernacular_text = await speech_processor.speech_to_text(
            wav_data, preferred_language
        )
        logger.info("Vernacular Text %s", vernacular_text)
        english_text = await translator.translate_text(
            vernacular_text,
            preferred_language,
            Language.EN,
        )
        logger.info("English Text %s", english_text)

    message = Message(
        message_type=MessageType.TEXT, text=TextMessage(body=english_text)
    )
    return message

async def handle_text_message(preferred_language: Language, message: TextMessage):
    messages = []
    if message.body:
        message.body = await translator.translate_text(
            message.body,
            Language.EN,
            preferred_language,
        )
    if message.header:
        message.header = await translator.translate_text(
            message.header, Language.EN, preferred_language
        )
    if message.footer:
        message.footer = await translator.translate_text(
            message.footer, Language.EN, preferred_language
        )
    logger.info("Vernacular Text %s", message.body)
    messages.append(
        Message(
            message_type=MessageType.TEXT,
            text=message
        )
    )
    try:
        audio_content = await speech_processor.text_to_speech(
            message.body, preferred_language
        )
        fid = str(uuid.uuid4())
        filename = f"{fid}.mp3"
        await storage.write_file(filename, audio_content, "audio/mpeg")
        media_output_url = await storage.make_public(filename)
        messages.append(
            Message(
                message_type=MessageType.AUDIO,
                audio=AudioMessage(media_url=media_output_url),
            )
        )
    except Exception as e:
        logger.error("Error in text to speech: %s", e)
    return messages

async def handle_document_message(preferred_language: Language, message: DocumentMessage):
    messages = []
    message.caption = await translator.translate_text(
        message.caption,
        Language.EN,
        preferred_language,
    )
    messages.append(
        Message(
            message_type=MessageType.DOCUMENT,
            document=message
        )
    )
    return messages

async def handle_image_message(preferred_language: Language, message: ImageMessage):
    messages = []
    message.caption = await translator.translate_text(
        message.caption,
        Language.EN,
        preferred_language,
    )
    messages.append(
        Message(
            message_type=MessageType.IMAGE,
            image=message
        )
    )
    return messages

async def handle_button_message(preferred_language: Language, message: ButtonMessage):
    messages = []
    for option in message.options:
        option.option_text = await translator.translate_text(
            option.option_text, Language.EN, preferred_language
        )
    message.body = await translator.translate_text(
        message.body,
        Language.EN,
        preferred_language,
    )
    message.header = await translator.translate_text(
        message.header, Language.EN, preferred_language
    )
    message.footer = await translator.translate_text(
        message.footer, Language.EN, preferred_language
    )
    messages.append(
        Message(
            message_type=MessageType.BUTTON,
            button=message
        )
    )
    try:
        audio_content = await speech_processor.text_to_speech(
            message.body, preferred_language
        )
        fid = str(uuid.uuid4())
        filename = f"{fid}.mp3"
        await storage.write_file(filename, audio_content, "audio/mpeg")
        audio_url = await storage.make_public(filename)
        messages.append(
            Message(
                message_type=MessageType.AUDIO,
                audio=AudioMessage(media_url=audio_url),
            )
        )
    except Exception as e:
        logger.error("Error in text to speech: %s", e)
    return messages

async def handle_list_message(preferred_language: Language, message: ListMessage):
    messages = []
    message.list_title = await translator.translate_text(
        message.list_title, Language.EN, preferred_language
    )
    message.button_text = await translator.translate_text(
        message.button_text, Language.EN, preferred_language
    )
    for option in message.options:
        option.option_text = await translator.translate_text(
            option.option_text, Language.EN, preferred_language
        )
    message.body = await translator.translate_text(
        message.body,
        Language.EN,
        preferred_language,
    )
    message.header = await translator.translate_text(
        message.header, Language.EN, preferred_language
    )
    message.footer = await translator.translate_text(
        message.footer, Language.EN, preferred_language
    )
    messages.append(
        Message(
            message_type=MessageType.OPTION_LIST,
            option_list=message
        )
    )
    try:
        audio_content = await speech_processor.text_to_speech(
            message.body, preferred_language
        )
        fid = str(uuid.uuid4())
        filename = f"{fid}.mp3"
        await storage.write_file(filename, audio_content, "audio/mpeg")
        audio_url = await storage.make_public(filename)
        messages.append(
            Message(
                message_type=MessageType.AUDIO,
                audio=AudioMessage(media_url=audio_url),
            )
        )
    except Exception as e:
        logger.error("Error in text to speech: %s", e)
    return messages

async def handle_output(preferred_language: Language, message: Message):
    logger.info("Preferred Language %s", preferred_language)
    logger.info("Message %s", message)

    message_type = message.message_type
    if message_type == MessageType.TEXT:
        messages = await handle_text_message(preferred_language, message.text)
        return messages
    elif message_type == MessageType.DOCUMENT:
        messages = await handle_document_message(preferred_language, message.document)
        return messages
    elif message_type == MessageType.IMAGE:
        messages = await handle_image_message(preferred_language, message.image)
        return messages
    elif message_type == MessageType.BUTTON:
        messages = await handle_button_message(preferred_language, message.button)
        return messages
    elif message_type == MessageType.OPTION_LIST:
        messages = await handle_button_message(preferred_language, message.option_list)
        return messages
    else:
        logger.error("Message Type not supported")
        return NotImplemented
