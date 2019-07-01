import json

from PIL import ImageDraw

from models import Conversation

with open('data.json') as f:
    conversation = Conversation(json.load(f))

screen = conversation.wallpaper
width, height = screen.size

draw = ImageDraw.Draw(screen)
draw.rectangle((0, 0, 720, 47), fill=(5, 76, 68))

draw.rectangle((0, 47, 720, 160), fill=(7, 94, 85))

draw.rectangle((0, 47, 720, 160), fill=(7, 94, 85))

screen.show()
