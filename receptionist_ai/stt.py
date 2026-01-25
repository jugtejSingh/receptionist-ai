import asyncio
from deepgram import AsyncDeepgramClient
from deepgram.core import EventType
import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

from receptionist_ai import make_call
from receptionist_ai.graph import agent

load_dotenv()

class DeepgramTranscriber:
    def __init__(self):
        self.client = AsyncDeepgramClient(api_key=os.getenv("DEEPGRAM_API"))
        self.connection = None
        self._cm = None
        self.deepgram_task = None

    async def start(self):
        """Initialize Deepgram connection"""
        cm = self.client.listen.v2.connect(
            model="flux-general-en",
            encoding="linear16",
            sample_rate="16000",

        )

        # Enter it and store both the CM and connection
        self.connection = await cm.__aenter__()
        self._cm = cm  # Store it for later

        # Handle transcription messages
        def on_message(message) -> None:
            print(f"DEBUG: Received message type: {getattr(message, 'type', 'Unknown')}")
            if hasattr(message, 'transcript') and message.transcript:
                # Calls the agent from the graph route
                make_call.messages_state.append(HumanMessage(content=message.transcript))
                result = agent.invoke({"messages": make_call.messages_state})
                print(f"DEBUG: {result}")
                make_call.messages_state = result["messages"]

                print(message.transcript)

        self.connection.on(EventType.MESSAGE, on_message)
        self.connection.on(EventType.ERROR, lambda error: print(f"Deepgram Error: {error}"))

        # Start listening in background
        self.deepgram_task = asyncio.create_task(self.connection.start_listening())

    async def send_audio(self, chunk: bytes):
        """Send audio chunk to Deepgram"""
        if self.connection:
            await self.connection._send(chunk)

    async def stop(self):
        """Close Deepgram connection"""
        try:
            if self.deepgram_task:
                self.deepgram_task.cancel()
                try:
                    await self.deepgram_task
                except asyncio.CancelledError:
                    pass

            if self._cm:
                await self._cm.__aexit__(None, None, None)
        except Exception as e:
            print(f"Error during Deepgram cleanup: {e}")