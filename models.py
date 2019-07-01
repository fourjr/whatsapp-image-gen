import random
import requests
from datetime import datetime
from enum import Enum
from io import BytesIO

from PIL import PILImage as PILImage

from utils import get_dimensions, get_member, get_message


__all__ = ('Image', 'Conversation', 'Metadata', 'Message', 'Member', 'Attachment', 'TickEnum')


class Image:
    def __init__(self, fp):
        if not fp.endswith('.png') and not fp.endswith('.jpg') and not fp.endswith('.jpeg'):
            raise ValueError('File is not a supported image type (jpg/png)')

        self.name = fp.split('/')[-1].replace('.png', '')
        self.file_path = fp
        self.size = get_dimensions(self.name)

        img = PILImage.open(self.file_path).convert('RGBA')
        self.image = img.resize(self.size, resample=PILImage.LANCZOS)


class Conversation:
    __slots__ = ('os', 'mode', 'warning', 'size', '_wallpaper', 'wallpaper_url', 'metadata', 'messages')

    def __init__(self, data):
        self.os = data['os'].lower()

        if self.os not in ('android'):
            raise ValueError('Only android is a support OS.')
            # TODO: Support iOS

        self.mode = data['mode']
        self.warning = data['warning']
        self.size = tuple(data['size'])
        self._wallpaper = None
        self.wallpaper_url = data['wallpaper']
        self.metadata = Metadata(self, data['metadata'])
        self.messages = [Message(self, i) for i in data['messages']]

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

        response = requests.get(self.icon_url)
        img = PILImage.open(BytesIO(response.content)).convert('RGBA')

        if img.size[0] != img.size[1]:
            raise ValueError('icon_url does not provide a square.')

        self.icon = img


class Message:
    __slots__ = ('_conversation', 'author', 'content', 'timestamp',
                 'attachment', 'starred', 'deleted', 'ticks', 'reply')

    def __init__(self, conversation, data):
        self._conversation = conversation

        self.author = get_member(conversation, data['author'])
        self.content = data['message']
        self.timestamp = datetime.strptime(data['timestamp'], r'%Y-%m-%dT%H:%M:%S.%fZ')
        self.attachment = Attachment(conversation, data['attachment']) if data['attachment'] else None
        self.starred = data['starred']
        self.deleted = data['deleted']
        self.ticks = TickEnum(data['ticks'])
        self.reply = get_message(conversation, data['reply']) if data['reply'] else None


class Member:
    __slots__ = ('_conversation', 'id', 'name', 'number', 'saved', 'me', 'hex_color', 'rgb_color')

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

        self.rgb_color = tuple(int(self.hex_color[i:i + 2], 16) for i in (0, 2, 4))


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
