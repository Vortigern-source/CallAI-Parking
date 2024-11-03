from pipecat.pipeline.task import FrameProcessor, FrameDirection
from pipecat.frames.frames import (
    Frame, 
    TTSStartedFrame, 
    TTSStoppedFrame,
    TTSAudioRawFrame,
    OutputAudioRawFrame
)
from loguru import logger
import asyncio
from typing import Optional, Dict
from collections import deque

class AudioCoordinatorProcessor(FrameProcessor):
    def __init__(self):
        super().__init__()
        self._current_segment: Optional[int] = None
        self._pending_segments: deque = deque()
        self._lock: asyncio.Lock = asyncio.Lock()
        
    async def process_frame(self, frame: Frame, direction: FrameDirection):
        try:
            async with self._lock:
                if isinstance(frame, TTSStartedFrame):
                    if self._current_segment is None:
                        self._current_segment = frame.id
                        await self.push_frame(frame, direction)
                        logger.debug(f"Started segment {frame.id}")
                    else:
                        self._pending_segments.append(frame.id)
                        logger.debug(f"Queued segment {frame.id}")
                
                elif isinstance(frame, TTSStoppedFrame):
                    if frame.id == self._current_segment:
                        await self.push_frame(frame, direction)
                        self._current_segment = None
                        
                        # Start next segment if any
                        if self._pending_segments:
                            next_id = self._pending_segments.popleft()
                            self._current_segment = next_id
                            await self.push_frame(TTSStartedFrame(id=next_id), direction)
                            logger.debug(f"Starting next segment {next_id}")
                
                elif isinstance(frame, (TTSAudioRawFrame, OutputAudioRawFrame)):
                    if hasattr(frame, 'id') and frame.id == self._current_segment:
                        await self.push_frame(frame, direction)
                        logger.debug(f"Playing audio frame for segment {self._current_segment}")
                
                else:
                    await self.push_frame(frame, direction)
                    
        except Exception as e:
            logger.error(f"Error in AudioCoordinatorProcessor: {str(e)}")
            self._current_segment = None
            self._pending_segments.clear()

    async def cleanup(self):
        """Clean up resources when shutting down"""
        logger.info("Cleaning up AudioCoordinator resources")
        self._current_segment = None
        self._pending_segments.clear()
