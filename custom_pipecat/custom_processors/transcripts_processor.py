from pipecat.pipeline.task import FrameProcessor, FrameDirection
from pipecat.frames.frames import (
    Frame,
    LLMMessagesFrame,
    LLMFullResponseStartFrame,
    LLMFullResponseEndFrame,
    TextFrame,
    OutputAudioRawFrame,
    BotSpeakingFrame,
)
from loguru import logger


# The class  handles partial bot responses that may not be fully captured in LLMMessagesFrames (usually at the end of the call when user hangs up)
class BotBufferProcessor(FrameProcessor):
    def __init__(self):
        super().__init__()
        self.name = "BotBuffer"
        self.bot_buffer = ""
        self.is_bot_speaking = False

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        # Deal with cases where the LLMMessagesFrame is not called, can happen at the end of the call if user hangs up
        if isinstance(frame, LLMFullResponseStartFrame):
            self.is_bot_speaking = True
            self.bot_buffer = ""
        elif self.is_bot_speaking and isinstance(frame, TextFrame):
            timestamp, word = frame.pts, frame.text
            self.bot_buffer += word + " "
        elif isinstance(frame, LLMFullResponseEndFrame):
            self.is_bot_speaking = False
            if self.bot_buffer:
                self.bot_buffer = ""
        await self.push_frame(frame, direction)


# This class processes frames to capture and manage the transcript of the conversation.
# It reads from the LLM context (messages) and generate a formatted transcript.
class TranscriptCaptureProcessor(FrameProcessor):
    def __init__(self):
        super().__init__()
        self.name = "TranscriptCapture"
        self.messages = []
        self.transcript = ""
        self.bot_buffer = ""
        self.is_bot_speaking = False

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        if not isinstance(frame, OutputAudioRawFrame) and not isinstance(frame, BotSpeakingFrame):
            logger.info(f"BasicFrameProcessor: {frame}")
        if isinstance(frame, LLMMessagesFrame):
            # logger.info(f'LLMMessagesFrame: {frame.messages}')
            self.messages = frame.messages

    def get_transcript(self, bot_buffer_processor: BotBufferProcessor):
        logger.info(f"Bot buffer: {self.bot_buffer}")
        for message in self.messages:
            if message["role"] == "assistant":
                self.transcript += f"BOT: {message['content']}\n"
            elif message["role"] == "user":
                self.transcript += f"USER: {message['content']}\n"
        # If final BOT message was not added to messages, we get it from the bot buffer
        if bot_buffer_processor.bot_buffer != "":
            self.transcript += f"BOT: {bot_buffer_processor.bot_buffer.strip()}\n"
        return self.transcript
