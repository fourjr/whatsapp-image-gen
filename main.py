import json
import os

from PIL import ImageDraw, ImageFont, Image

from models import Conversation, ImageTextDraw, Icon
from utils import get_text_size_box, Colors

with open('data.json') as f:
    conversation = Conversation(json.load(f))

images = {}
for i in os.listdir('images'):
    if i.endswith('.png'):
        images[i.replace('.png', '')] = Icon('images/' + i)

# TODO: FIND A WAY TO MAKE THIS INFINITE AND NOT LIMITED BY "10"
screen = Image.new('RGBA', (conversation.size[0], conversation.size[1] * 10), (0, 0, 0, 0))
wallpaper = conversation.wallpaper
s_width, s_height = screen.size

screen.alpha_composite(wallpaper, (0, conversation.size[1] * 9))

# messages
y = s_height - 120
previous_author = None
for msg in conversation.messages:
    image = msg.generate_image()
    m_width, m_height = image.size

    if previous_author == msg.author.me:
        y -= m_height
    else:
        y -= 10 + m_height

    if y < 0:
        break

    if msg.author.me:
        x = s_width - 35 - m_width
    else:
        x = 0 + 35

    screen.alpha_composite(image, (x, y))
    y -= 5

# screen.show()
screen = screen.crop((0, conversation.size[1] * 9, s_width, s_height))

# others
draw = ImageTextDraw(screen)
draw.rectangle((0, 0, 720, 47), fill=(5, 76, 68))

draw.rectangle((0, 47, 720, 160), fill=(7, 94, 85))

draw.rectangle((0, 47, 720, 160), fill=(7, 94, 85))

s_width, s_height = screen.size
print(screen.size)

## textbox

textbox = screen.crop((0, 1365, s_width, s_height))
textbox_draw = ImageTextDraw(textbox)
t_width, t_height = textbox.size
# textbox.alpha_composite(images['emoji'], )
textbox_draw.rounded_rectangle((10, 10, t_width - 110, t_height - 10), 50, Colors.WHITE)

img_size = t_height - 10 - 10 - 50
emoji = images['emoji'].generate_image((img_size, img_size))
textbox.alpha_composite(emoji, (30, 35))

textbox_draw.text((30 + img_size + 20, 35), 'Type a message', fill=Colors.LIGHT_GREY, font=conversation.font_40)

attach = images['attach'].generate_image((img_size, img_size))
textbox.alpha_composite(attach, (t_width - 110 - 160, 35))

camera = images['camera'].generate_image((img_size, img_size))
textbox.alpha_composite(camera, (t_width - 110 - 70, 35))

# size = 100
textbox_draw.ellipse((t_width - 100, 10, t_width - 10, t_height - 10), fill=Colors.GREEN)

mic = images['microphone'].generate_image((img_size, img_size))
textbox.alpha_composite(mic, (t_width - 77, 35))

# textbox.show()

screen.alpha_composite(textbox, (0, 1365))
screen.show()
# screen.save('yes.png')
