import random
import requests
from datetime import datetime
from enum import Enum
from io import BytesIO

from PIL import Image as PILImage
from PIL import ImageDraw, ImageFont

from utils import get_dimensions, get_member, get_message, get_text_size_box, Colors


__all__ = ('ImageTextDraw', 'Image', 'Conversation', 'Metadata', 'Message', 'Member', 'Attachment', 'TickEnum')


class ImageTextDraw(ImageDraw.ImageDraw):

    def text_box(self, coordinates, full_text, color, font, box_width, spacing):
        # Adapted from https://gist.github.com/turicas/1455973
        x, y = coordinates

        size, text_height, lines = get_text_size_box(box_width, font, full_text, spacing)

        for nl in lines:
            for index, line in enumerate(nl):
                self.text((x, y), line, font=font, fill=color)
                y += text_height

            y += spacing

        return (x, y + size[1])
        # returns the x and y value right below the last text

    def rounded_rectangle(self, coordinates, radius, fill):
        x0, y0, x1, y1 = coordinates
        diameter = radius * 2

        self.pieslice((x0, x0, diameter, diameter), 180, 270, fill=fill)  # top left
        self.pieslice((x0, y1 - diameter, diameter, y1), 90, 180, fill=fill)  # bottom left
        self.pieslice((x1 - diameter, y0, x1, diameter), 270, 360, fill=fill)  # top right
        self.pieslice((x1 - diameter, y1 - diameter, x1, y1), 0, 90, fill=fill)  # bottom right

        self.rectangle((radius, x0, x1 - radius, y1), fill=fill)  # middle rectangle
        self.rectangle((x0, radius, radius + x0, y1 - radius), fill=fill)  # left rectangle
        self.rectangle((x1 - radius, radius, x1, y1 - radius), fill=fill)  # right rectangle


class Icon:
    def __init__(self, fp):
        if not fp.endswith('.png') and not fp.endswith('.jpg') and not fp.endswith('.jpeg'):
            raise ValueError('File is not a supported image type (jpg/png)')

        self.name = fp.split('/')[-1].replace('.png', '')
        self.file_path = fp
        self.size = get_dimensions(self.name)

    def generate_image(self, size):
        img = PILImage.open(self.file_path).convert('RGBA')
        return img.resize(size or self.size, resample=PILImage.LANCZOS)


class Conversation:
    __slots__ = ('os', 'font', 'font_40', 'bold_font', 'mode', 'warning', 'size', 'wallpaper', 'wallpaper_url', 'metadata', 'messages', 'sorted_messages')

    def __init__(self, data):
        self.os = data['os'].lower()
        self.font = ImageFont.truetype(f'fonts/{self.os.title()}.ttf', 35)
        self.font_40 = ImageFont.truetype(f'fonts/{self.os.title()}.ttf', 40)
        self.bold_font = ImageFont.truetype(f'fonts/{self.os.title()}-Bold.ttf', 35)

        if self.os not in ('android'):
            raise ValueError('Only android is a support OS.')
            # TODO: Support iOS

        self.mode = data['mode']
        self.warning = data['warning']
        self.size = tuple(data['size'])
        self.wallpaper_url = data['wallpaper']
        self.metadata = Metadata(self, data['metadata'])
        self.messages = [Message(self, i) for i in data['messages']]
        self.sorted_messages = sorted(self.messages, key=lambda x: x.timestamp)

        if self.wallpaper_url:
            response = requests.get(self.wallpaper_url)
            img = PILImage.open(BytesIO(response.content)).convert('RGBA')
        else:
            img = PILImage.open('images/wallpaper.png')

        self.wallpaper = img.resize(self.size, resample=PILImage.LANCZOS)


class Metadata:
    __slots__ = ('_conversation', 'group_name', 'icon_url', '_icon', 'last_seen', 'members')

    def __init__(self, conversation, data):
        self._conversation = conversation
        self.group_name = data['name']
        self.icon_url = data['icon_url']
        self._icon = None

        self.last_seen = data['lastSeen']
        self.members = [Member(conversation, i) for i in data['members']]

        if self.icon_url:
            response = requests.get(self.icon_url)
            img = PILImage.open(BytesIO(response.content)).convert('RGBA')

            if img.size[0] != img.size[1]:
                raise ValueError('icon_url does not provide a square.')

            self.icon = img


class Message:
    __slots__ = ('_conversation', 'author', 'content', 'cut_content', 'timestamp',
                 'attachment', 'starred', 'deleted', 'ticks', 'reply')

    def __init__(self, conversation, data):
        self._conversation = conversation

        self.author = get_member(conversation, data['author'])
        self.content = data['message']

        if len(self.content) > 768:
            self.cut_content = self.content[:768] + '... [Read more]'
        else:
            self.cut_content = self.content

        self.timestamp = datetime.strptime(data['timestamp'], r'%Y-%m-%dT%H:%M:%S.%fZ')
        self.attachment = Attachment(conversation, data['attachment']) if data['attachment'] else None
        self.starred = data['starred']
        self.deleted = data['deleted']
        self.ticks = TickEnum(data['ticks'])
        self.reply = get_message(conversation, data['reply']) if data['reply'] else None

    def generate_image(self):
        size, text_height, lines = get_text_size_box(530, self._conversation.font, self.cut_content, spacing=4)
        size = [size[0] + 17 * 2, size[1] + 13 * 2]
        if not self.author.me:
            size[1] += 50
            offset = 50
            color = Colors.OTHER
        else:
            offset = 0
            color = Colors.SELF

        message = PILImage.new('RGBA', size, (0, 0, 0, 0))  # (255, 255, 255, 0)
        message_draw = ImageTextDraw(message)

        width, height = message.size

        # rounded rectangle
        message_draw.rounded_rectangle((0, 0, width, height), 15, fill=color)

        message_draw.text_box((17, 13 + offset), self.cut_content, (0, 0, 0), self._conversation.font, 530, spacing=4)

        if not self.author.me:
            message_draw.text((17, 13), self.author.name, self.author.rgb_color, self._conversation.bold_font)

        return message


class Member:
    __slots__ = ('_conversation', 'id', 'name', 'number', 'saved', 'me', 'hex_color')

    def __init__(self, conversation, data):
        self._conversation = conversation

        self.id = data['id']
        self.name = data['name']
        self.number = data['number']

        if not self.number.startswith('+'):
            raise ValueError(f'Include the country code in the member number ({self.number})')

        self.saved = data['saved']
        self.me = data['me']
        self.hex_color = data['color']

        if self.hex_color is None:
            colors = ['#6bcbef', '#e542a3', '#91ab01', '#dfb610', '#b4876e',
                      '#8b7add', '#fe7c7f', '#b04632', '#ff8f2c', '#3bdec3',
                      '#c90379', '#59d368', '#fd85d4', '#8393ca', '#ba33dc',
                      '#ffa97a', '#1f7aec', '#029d00', '#35cd96']
            # default colors from whatsapp
            self.hex_color = random.choice(colors)

        if isinstance(self.hex_color, int):
            self.hex_color = hex(self.hex_color).lstrip('0x')
        elif self.hex_color.startswith('#'):
            self.hex_color = self.hex_color.lstrip('#')
        else:
            raise ValueError(f'Invalid color argument ({self.hex_color}) in member')

    @property
    def rgb_color(self):        
        return tuple(int(self.hex_color[i:i + 2], 16) for i in (0, 2, 4))


class Attachment:
    __all__ = ('_conversation', 'url', 'filename', 'image')

    def __init__(self, conversation, data):
        self._conversation = conversation
        self.url = data['url']
        self.filename = data['filename']
        self.image = data['image']

    # TOOD: Insert a property to get a thumbnail-sized image
    # If self.image is true, use the thumbnail of "url" or else use those that
    # whatsapp uses


class TickEnum(Enum):
    single_tick = 0
    grey_tick = 1
    blue_tick = 2
