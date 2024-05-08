"""
Handlers for Language Input and Output
"""

import logging
import uuid
from extension import speech_processor, storage, translator
from lib.audio_converter import convert_to_wav_with_ffmpeg
from lib.data_models import (
    ChannelIntent,
    LanguageIntent,
    MessageType,
    Message,
    Flow,
    FlowIntent,
    UserInput,
    TextMessage,
    AudioMessage,
    ListMessage,
    ButtonMessage,
    DocumentMessage,
    ImageMessage,
    FormMessage,
    Channel,
)
from lib.model import Language


logger = logging.getLogger("language")
logger.setLevel(logging.INFO)


async def handle_input(preferred_language: Language, message: Message) -> str:
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


async def handle_output(preferred_language: Language, message: Message):
    logger.info("Preferred Language %s", preferred_language)
    logger.info("Message %s", message)

    messages = []
    message_type = message.message_type
    if message_type == MessageType.TEXT:
        if message.text.body:
            message.text.body = await translator.translate_text(
                message.text.body,
                Language.EN,
                preferred_language,
            )
        if message.text.header:
            message.text.header = await translator.translate_text(
                message.text.header, Language.EN, preferred_language
            )
        if message.text.footer:
            message.text.footer = await translator.translate_text(
                message.text.footer, Language.EN, preferred_language
            )
        logger.info("Vernacular Text %s", message.text.body)
        messages.append(message)
        try:
            audio_content = await speech_processor.text_to_speech(
                message.text.body, preferred_language
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
    elif message_type == MessageType.DOCUMENT:
        message.document.caption = await translator.translate_text(
            message.document.caption,
            Language.EN,
            preferred_language,
        )
        messages.append(message)
        return messages
    elif message_type == MessageType.IMAGE:
        message.image.caption = await translator.translate_text(
            message.image.caption,
            Language.EN,
            preferred_language,
        )
        messages.append(message)
        return messages
    elif message_type == MessageType.INTERACTIVE:
        message.interactive.body = await translator.translate_text(
            message.interactive.body,
            Language.EN,
            preferred_language,
        )
        message.interactive.header = await translator.translate_text(
            message.interactive.header, Language.EN, preferred_language
        )
        message.interactive.footer = await translator.translate_text(
            message.interactive.footer, Language.EN, preferred_language
        )
        if isinstance(message.interactive, ListMessage):
            message.interactive.list_title = await translator.translate_text(
                message.interactive.list_title, Language.EN, preferred_language
            )
            message.interactive.button_text = await translator.translate_text(
                message.interactive.button_text, Language.EN, preferred_language
            )
            for option in message.interactive.options:
                option.option_text = await translator.translate_text(
                    option.option_text, Language.EN, preferred_language
                )
        elif isinstance(message.interactive, ButtonMessage):
            for option in message.interactive.options:
                option.option_text = await translator.translate_text(
                    option.option_text, Language.EN, preferred_language
                )
        else:
            return NotImplemented
        messages.append(message)
        try:
            audio_content = await speech_processor.text_to_speech(
                message.interactive.body, preferred_language
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
    else:
        logger.error("Message Type not supported")
        return NotImplemented
