from deepgram import DeepgramClient

client = DeepgramClient()

response = client.speak.v1.audio.generate(
    text="Hello, this is a sample text to speech conversion."
)

# Save the audio file
with open("output.mp3", "wb") as audio_file:
    audio_file.write(response.stream.getvalue())