from pipecat.pipeline.task import FrameProcessor, FrameDirection
import time
from pipecat.frames.frames import (
    Frame,
    BotStartedSpeakingFrame,
    BotStoppedSpeakingFrame,
    TranscriptionFrame,
    BotInterruptionFrame,
    LLMMessagesAppendFrame,
    TTSStoppedFrame,
)
from loguru import logger
import asyncio


# Debugging tool to print all frames
# class InterruptionFrameProcessor(FrameProcessor):
#     def __init__(self):
#         super().__init__()
#         self.name = "InterruptionFrameProcessor"
#         self.bot_started_speaking = False

#     async def process_frame(self, frame: Frame, direction: FrameDirection):
#         if isinstance(frame, BotStartedSpeakingFrame):
#             self.bot_started_speaking = True
#             logger.info(f"InterruptionFrameProcessor bot started speaking")
#         elif isinstance(frame, BotStoppedSpeakingFrame):
#             self.bot_started_speaking = False
#             logger.info(f"InterruptionFrameProcessor bot stopped speaking")
#         elif isinstance(frame, TranscriptionFrame):
#             logger.info(f"InterruptionFrameProcessor transcription frame: {frame}")
#             if self.bot_started_speaking:
#                 logger.info(f"InterruptionFrameProcessor sending interruption frame: {frame}")
#                 await self.push_frame(BotInterruptionFrame(), direction=FrameDirection.UPSTREAM)
#                 # Context aggregator expects a user started speaking and user ended speaking to aggregate correctly, hacky way to make sure we aggregate correctly
#                 # Not tested yet
#                 await self.push_frame(
#                     LLMMessagesAppendFrame(messages=[{"role": "user", "content": frame.text}]),
#                     direction=direction,
#                 )
#         await self.push_frame(frame, direction)


class InterruptionFrameProcessor(FrameProcessor):
    def __init__(self):
        super().__init__()
        self.name = "InterruptionFrameProcessor"
        self.bot_started_speaking = False
        self.last_interruption_time = None
        self.interruption_in_progress = False
        self._lock = asyncio.Lock()  # Add lock for thread safety

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        try:
            if isinstance(frame, BotStartedSpeakingFrame):
                self.bot_started_speaking = True
                self.interruption_in_progress = False
                logger.info("InterruptionFrameProcessor bot started speaking")
                await self.push_frame(frame, direction)

            elif isinstance(frame, BotStoppedSpeakingFrame):
                self.bot_started_speaking = False
                logger.info("InterruptionFrameProcessor bot stopped speaking")
                await self.push_frame(frame, direction)

            elif isinstance(frame, TranscriptionFrame) and self.bot_started_speaking:
                current_time = time.time()

                async with self._lock:  # Use lock for atomic operations
                    if (
                        not self.last_interruption_time
                        or current_time - self.last_interruption_time > 1.0
                    ) and not self.interruption_in_progress:
                        logger.info("InterruptionFrameProcessor sending interruption frame")
                        self.last_interruption_time = current_time
                        self.interruption_in_progress = True

                        try:
                            # Create all frames first to ensure atomic operation
                            frames_to_push = [
                                (TTSStoppedFrame(), FrameDirection.UPSTREAM),
                                (BotStoppedSpeakingFrame(), FrameDirection.UPSTREAM),
                                (BotInterruptionFrame(), FrameDirection.UPSTREAM),
                                (
                                    LLMMessagesAppendFrame(
                                        messages=[{"role": "user", "content": frame.text.strip()}]
                                    ),
                                    direction,
                                ),
                                (frame, direction),
                            ]

                            # Push all frames in sequence
                            for f, d in frames_to_push:
                                await self.push_frame(f, d)

                        finally:
                            self.interruption_in_progress = False
                    else:
                        # If we're in cooldown or already processing an interruption,
                        # just push the frame through
                        await self.push_frame(frame, direction)
            else:
                await self.push_frame(frame, direction)

        except Exception as e:
            logger.error(f"Error in InterruptionFrameProcessor: {e}")
            self.interruption_in_progress = False
            raise
