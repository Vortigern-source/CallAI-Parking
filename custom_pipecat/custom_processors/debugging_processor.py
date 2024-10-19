from pipecat.pipeline.task import FrameProcessor, FrameDirection
from pipecat.frames.frames import Frame
from loguru import logger


class DebuggingFrameProcessor(FrameProcessor):
    async def process_frame(self, frame: Frame, direction: FrameDirection):
        logger.debug(f"Frame: {type(frame).__name__}, Direction: {direction.name}")
        await self.push_frame(frame)
