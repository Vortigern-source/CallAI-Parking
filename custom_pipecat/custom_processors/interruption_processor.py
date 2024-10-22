from pipecat.pipeline.task import FrameProcessor, FrameDirection
from pipecat.frames.frames import (
    Frame,
    BotStartedSpeakingFrame,
    BotStoppedSpeakingFrame,
    TranscriptionFrame,
    BotInterruptionFrame,
    LLMMessagesAppendFrame,
)

from loguru import logger


# Debugging tool to print all frames
class InterruptionFrameProcessor(FrameProcessor):
    def __init__(self):
        super().__init__()
        self.name = "InterruptionFrameProcessor"
        self.bot_started_speaking = False

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        if isinstance(frame, BotStartedSpeakingFrame):
            self.bot_started_speaking = True
            logger.info(f"InterruptionFrameProcessor bot started speaking")
        elif isinstance(frame, BotStoppedSpeakingFrame):
            self.bot_started_speaking = False
            logger.info(f"InterruptionFrameProcessor bot stopped speaking")
        elif isinstance(frame, TranscriptionFrame):
            logger.info(f"InterruptionFrameProcessor transcription frame: {frame}")
            if self.bot_started_speaking:
                logger.info(f"InterruptionFrameProcessor sending interruption frame: {frame}")
                await self.push_frame(BotInterruptionFrame(), direction=FrameDirection.UPSTREAM)
                # Context aggregator expects a user started speaking and user ended speaking to aggregate correctly, hacky way to make sure we aggregate correctly
                # Not tested yet
                await self.push_frame(
                    LLMMessagesAppendFrame(messages=[{"role": "user", "content": frame.text}]),
                    direction=direction,
                )
        await self.push_frame(frame, direction)
