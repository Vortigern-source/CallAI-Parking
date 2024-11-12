import os
from twilio.rest import Client
from pipecat.frames.frames import EndFrame, TTSSpeakFrame, EndTaskFrame, FrameDirection


async def hangup_call(function_name, tool_call_id, args, llm, context, result_callback):
    print("End call fucntion called")
    print(f"Function name: {function_name}")
    print(f"Context: {context}")
    for key, value in args.items():
        print(f"{key}: {value}")

    # final_message = args["final_message"]
    # start = 0
    # # while start < len(final_message):
    # #     end_position = match_endofsentence(final_message[start:])
    # #     if end_position == 0:
    # #         # No more sentence-ending punctuation found, push the rest of the message
    # #         await llm.push_frame(TTSSpeakFrame(final_message[start:].strip()))
    # #         break
    # #     else:
    # #         # Push the sentence up to the found punctuation
    # #         end = start + end_position
    # #         await llm.push_frame(TTSSpeakFrame(final_message[start:end].strip()))
    # #         start = end
    await llm.push_frame(EndTaskFrame(), FrameDirection.UPSTREAM)
