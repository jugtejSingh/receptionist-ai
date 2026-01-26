import os
import logging

from deepgram import DeepgramClient

class DeepgramTTS:
    def __init__(self):
        self.deepgram = DeepgramClient(api_key=os.getenv("DEEPGRAM_API"))
        self.response = None
        self.name = "test.mp3"

    def convertTextToAudio(self, text):
        try:
            self.response = self.deepgram.speak.v1.audio.generate(
                text=text,
                model="aura-2-thalia-en"
            )

            # Save the audio file
            with open(self.name, "wb") as audio_file:
                audio_file.write(self.response.stream.getvalue())

            print(f"Audio saved to test.mp3")
            return self.name

        except Exception as e:
            print(f"Exception: {e}")
