from pipecat.pipeline.task import FrameProcessor, FrameDirection
from pipecat.frames.frames import (
    Frame,
    LLMMessagesFrame,
    LLMFullResponseStartFrame,
    LLMFullResponseEndFrame,
    TextFrame,
    OutputAudioRawFrame,
    BotSpeakingFrame,
    LLMMessagesAppendFrame,
)
from loguru import logger


# The class  handles partial bot responses that may not be fully captured in LLMMessagesFrames (usually at the end of the call when user hangs up)
# class BotBufferProcessor(FrameProcessor):
#     def __init__(self):
#         super().__init__()
#         self.name = "BotBuffer"
#         self.bot_buffer = ""
#         self.is_bot_speaking = False

#     async def process_frame(self, frame: Frame, direction: FrameDirection):
#         # Deal with cases where the LLMMessagesFrame is not called, can happen at the end of the call if user hangs up
#         if isinstance(frame, LLMFullResponseStartFrame):
#             self.is_bot_speaking = True
#             self.bot_buffer = ""
#         elif self.is_bot_speaking and isinstance(frame, TextFrame):
#             timestamp, word = frame.pts, frame.text
#             self.bot_buffer += word + " "
#         elif isinstance(frame, LLMFullResponseEndFrame):
#             self.is_bot_speaking = False
#             if self.bot_buffer:
#                 self.bot_buffer = ""
#         await self.push_frame(frame, direction)


class BotBufferProcessor(FrameProcessor):
    def __init__(self):
        super().__init__()
        self.name = "BotBuffer"
        self.bot_buffer = ""
        self.is_bot_speaking = False
        self.current_message = None
        self.pending_frames = []

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        try:
            if isinstance(frame, LLMFullResponseStartFrame):
                # Clear any pending frames when starting new response
                self.pending_frames = []
                self.is_bot_speaking = True
                self.bot_buffer = ""
                self.current_message = None
                await self.push_frame(frame, direction)

            elif self.is_bot_speaking and isinstance(frame, TextFrame):
                self.bot_buffer += frame.text + " "
                # Store frame to maintain order
                self.pending_frames.append((frame, direction))

            elif isinstance(frame, LLMFullResponseEndFrame):
                if self.bot_buffer:
                    self.current_message = self.bot_buffer.strip()
                    # Create context frame
                    context_frame = LLMMessagesAppendFrame(
                        messages=[{"role": "assistant", "content": self.current_message}]
                    )
                    # Push context frame first
                    await self.push_frame(context_frame, direction)

                    # Push all pending text frames in order
                    for pending_frame, pending_direction in self.pending_frames:
                        await self.push_frame(pending_frame, pending_direction)

                # Reset state
                self.is_bot_speaking = False
                self.bot_buffer = ""
                self.current_message = None
                self.pending_frames = []

                # Push end frame last
                await self.push_frame(frame, direction)

            else:
                # For non-bot-speaking frames, push immediately
                await self.push_frame(frame, direction)

        except Exception as e:
            logger.error(f"Error in BotBufferProcessor: {e}")
            # Reset state if something goes wrong
            self.is_bot_speaking = False
            self.bot_buffer = ""
            self.current_message = None
            self.pending_frames = []
            raise


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
