import json

from PIL import Image

from models import Conversation, ImageTextDraw

with open('data.json') as f:
    conversation = Conversation(json.load(f))

# TODO: FIND A WAY TO MAKE THIS INFINITE AND NOT LIMITED BY "10"
screen = Image.new('RGBA', (conversation.size[0], conversation.size[1] * 10), (0, 0, 0, 0))
wallpaper = conversation.generate_wallpaper()
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

screen = screen.crop((0, conversation.size[1] * 9, s_width, s_height))

width, height = screen.size

# bars
draw = ImageTextDraw(screen)

notification_bar = conversation.generate_notification_bar()
top_bar = conversation.generate_top_bar()
bottom_bar = conversation.generate_bottom_bar()

screen.alpha_composite(notification_bar, (0, 0))
screen.alpha_composite(top_bar, (0, 47))
screen.alpha_composite(bottom_bar, (0, height - 115))

screen.show()
# screen.save('yes.png')
