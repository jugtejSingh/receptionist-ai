import asyncio
from deepgram import AsyncDeepgramClient, DeepgramClient
from deepgram.core import EventType
import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

from receptionist_ai import make_call
from receptionist_ai.audio_converter import convert_and_send_to_twilio
from receptionist_ai.graph import agent

load_dotenv()

class DeepgramTranscriber:
    def __init__(self, ws = None, stream_sid = None):
        self.client = AsyncDeepgramClient(api_key=os.getenv("DEEPGRAM_API"))
        self.connection = None
        self._cm = None
        self.deepgram_task = None
        self.ws = ws
        self.stream_sid = stream_sid

    async def start(self):
        """Initialize Deepgram connection"""
        cm = self.client.listen.v2.connect(
            model="flux-general-en",
            encoding="linear16",
            sample_rate="16000",
            eot_threshold="0.75",
        )

        # Enter it and store both the CM and connection
        self.connection = await cm.__aenter__()
        self._cm = cm  # Store it for later

        # Handle transcription messages
        async def on_message(message) -> None:
            if hasattr(message, 'type') and message.type == 'TurnInfo':
                if hasattr(message, 'event') and message.event == 'EndOfTurn':
                    # Calls the agent from the graph route
                    make_call.messages_state.append(HumanMessage(content=message.transcript))
                    result = agent.invoke({"messages": make_call.messages_state})
                    make_call.messages_state = result["messages"]
                    print(make_call.messages_state[-1].content)
                    # TTS CODE
                    tts_client = AsyncDeepgramClient(api_key=os.getenv("DEEPGRAM_API"))

                    response = tts_client.speak.v1.audio.generate(
                        text=make_call.messages_state[-1].content
                    )

                    temp_mp3 = "temp_output.mp3"
                    with open(temp_mp3, "wb") as audio_file:
                        async for chunk in response:
                            audio_file.write(chunk)

                    await convert_and_send_to_twilio(temp_mp3,self.ws,self.stream_sid)

                    if os.path.exists(temp_mp3):
                        os.remove(temp_mp3)


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