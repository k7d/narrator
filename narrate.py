import os
import sys
import  threading

from openai import OpenAI
import base64
import json
import time
import simpleaudio as sa
import errno
from elevenlabs import generate, play, voices
from PIL import Image, ExifTags
import matplotlib.pyplot as plt

client = OpenAI()

def show_image(image_path):
    image = Image.open(image_path)

    # Correct orientation based on EXIF data
    try:
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break
        exif = dict(image._getexif().items())

        if exif[orientation] == 3:
            image = image.rotate(180, expand=True)
        elif exif[orientation] == 6:
            image = image.rotate(270, expand=True)
        elif exif[orientation] == 8:
            image = image.rotate(90, expand=True)
    except (AttributeError, KeyError, IndexError):
        # Cases: image doesn't have getexif
        pass

    image.show()

def encode_image(image_path):
    while True:
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode("utf-8")
        except IOError as e:
            if e.errno != errno.EACCES:
                # Not a "file in use" error, re-raise
                raise
            # File is being written to, wait a bit and retry
            time.sleep(0.1)

voice_ids = {
    "david": "5hLaAvfSnWWJYGR70qsb",
    "ricky": "fkvTXkoC5u01kASwEV3i",
}

def play_audio(text, style):
    audio = generate(text=text, voice=voice_ids[style], model="eleven_turbo_v2")

    unique_id = base64.urlsafe_b64encode(os.urandom(30)).decode("utf-8").rstrip("=")
    dir_path = os.path.join("narration", unique_id)
    os.makedirs(dir_path, exist_ok=True)
    file_path = os.path.join(dir_path, "audio.wav")

    with open(file_path, "wb") as f:
        f.write(audio)

    play(audio)


user_prompts = {
    "david": "Describe this image",
    "ricky": "Roast this image",
}


def generate_user_prompt(base64_image, style):
    return {
        "role": "user",
        "content": [
            {"type": "text", "text": user_prompts[style]},
            {
                "type": "image_url",
                "image_url": f"data:image/jpeg;base64,{base64_image}",
            },
        ],
    }


systems_prompts = {
    #     "david": """
    # You are Sir David Attenborough. Narrate the picture of the human as if it is a nature documentary.
    # Make it snarky and funny. Don't repeat yourself. Make it short. If I do anything remotely interesting, make a big deal about it!
    # """,
    "david": """
You are Sir David Attenborough. Narrate what is shown in the picture as if it is a nature documentary.
Make it snarky and funny. Don't repeat yourself. Make it short. If there is anything remotely interesting in picture, make a big deal about it!
""",
    "ricky": """
You are comedian Ricky Gervais. Roast what is shown in the picture as if you were doing a comedy show.
Make it snarky and funny. Don't repeat yourself. Make it short. If there is anything remotely interesting in picture, make a big deal about it!
""",
}


def generate_system_prompt(style):
    return {
        "role": "system",
        "content": systems_prompts[style],
    }


def analyze_image(base64_image, script, style):
    response = client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=[generate_system_prompt(style)]
                 + script
                 + [generate_user_prompt(base64_image, style)],
        max_tokens=1024,
    )
    response_text = response.choices[0].message.content
    return response_text


def main(style, photo):
    script = []

    # path to your image
    image_path = os.path.join(os.getcwd(), photo)
    show_image(image_path)

    # getting the base64 encoding
    base64_image = encode_image(image_path)

    # analyze posture
    print("Generating text...")
    analysis = analyze_image(base64_image, script=script, style=style)

    print(analysis)

    print("Generating voice...")
    play_audio(analysis, style)

    # while True:
    #     # path to your image
    #     image_path = os.path.join(os.getcwd(), "./frames/frame.jpg")
    #
    #     # getting the base64 encoding
    #     base64_image = encode_image(image_path)
    #
    #     # analyze posture
    #     print("👀 David is watching...")
    #     analysis = analyze_image(base64_image, script=script)
    #
    #     print("🎙️ David says:")
    #     print(analysis)
    #
    #     play_audio(analysis)
    #
    #     script = script + [{"role": "assistant", "content": analysis}]
    #
    #     # wait for 5 seconds
    #     time.sleep(5)


if __name__ == "__main__":
    style = sys.argv[1] if len(sys.argv) > 1 else "david"
    photo = sys.argv[2] if len(sys.argv) > 2 else "./frames/frame.jpg"
    main(style, photo)
