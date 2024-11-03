from pipecat.pipeline.task import FrameProcessor, FrameDirection
from pipecat.frames.frames import Frame, BotStartedSpeakingFrame, BotStoppedSpeakingFrame, TranscriptionFrame, BotInterruptionFrame, LLMMessagesAppendFrame, UserStartedSpeakingFrame, UserStoppedSpeakingFrame, StartInterruptionFrame, StopInterruptionFrame

from loguru import logger


# Debugging tool to print all frames
class InterruptionFrameProcessor(FrameProcessor):
    def __init__(self):
        super().__init__()
        self.name = "InterruptionFrameProcessor"
        self.between_user_start_stop_speaking = False

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        if isinstance(frame, UserStartedSpeakingFrame):
            self.between_user_start_stop_speaking = True
            logger.info(f'InterruptionFrameProcessor user started speaking')
        elif isinstance(frame, UserStoppedSpeakingFrame):
            self.between_user_start_stop_speaking = False
            logger.info(f'InterruptionFrameProcessor user stopped speaking')
        elif isinstance(frame, TranscriptionFrame):
            logger.info(f'InterruptionFrameProcessor transcription frame: {frame}')
            # TODO: if transcription frame outside user started speaking - user stopped speaking, send interruption frame
            if not self.between_user_start_stop_speaking:
                logger.info(f'InterruptionFrameProcessor sending interruption frame: {frame}')
                await self.push_frame(StartInterruptionFrame(), direction=FrameDirection.DOWNSTREAM)
                await self.push_frame(frame, direction=direction)
                await self.push_frame(StopInterruptionFrame(), direction=direction)
                # Context aggregator expects a user started speaking and user ended speaking to aggregate correctly, hacky way to make sure we aggregate correctly
                # Not tested yet
                # await self.push_frame(LLMMessagesAppendFrame(messages=[{"role": "user", "content": frame.text}]), direction=direction)
                return
        await self.push_frame(frame, direction)


# if is_final:
            
    # await self._input.process_frame(StartInterruptionFrame(), FrameDirection.DOWNSTREAM)
    # # Stop bot frame before processing transcription
    # try:
    #     context = self._user_context_processor._context
    #     context.add_message({
    #         "role": "user",
    #         "content": frame.text
    #     })
    #     context_frame = OpenAILLMContextFrame(context)
    #     await self._user_context_processor.process_frame(context_frame, FrameDirection.DOWNSTREAM)
    # except Exception as e:
    #     logger.error(f"Error processing OpenAILLMContextFrame: {str(e)}")
    #     # Handle the error appropriately

    # await self._input.process_frame(StopInterruptionFrame(), FrameDirection.DOWNSTREAM)