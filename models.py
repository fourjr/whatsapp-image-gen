import random
import requests
import os
from datetime import datetime
from enum import Enum
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont

from utils import get_member, get_message, get_text_size_box, Colors


__all__ = ('ImageTextDraw', 'Icon', 'Conversation', 'Metadata', 'Message', 'Member', 'Attachment', 'TickEnum')


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

    def generate_image(self, size=None):
        img = Image.open(self.file_path).convert('RGBA')

        if size:
            img = img.resize(size, resample=Image.LANCZOS)

        return img


class Conversation:
    __slots__ = ('os', 'font_multiplier', 'font_25', 'font_35', 'font_40', 'bold_font_35', 'mode', 'warning', 'size', 'wallpaper_url', 'metadata', 'messages', 'sorted_messages', 'images')

    def __init__(self, data):
        self.os = data['os'].lower()
        self.font_multiplier = data['fontMultiplier']
        self.font_25 = ImageFont.truetype(f'fonts/{self.os.title()}.ttf', round(self.font_multiplier * 25))
        self.font_35 = ImageFont.truetype(f'fonts/{self.os.title()}.ttf', round(self.font_multiplier * 35))
        self.bold_font_35 = ImageFont.truetype(f'fonts/{self.os.title()}-Bold.ttf', round(self.font_multiplier * 35))
        self.font_40 = ImageFont.truetype(f'fonts/{self.os.title()}.ttf', round(self.font_multiplier * 40))

        if self.os not in {'android', 'ios'}:
            raise ValueError('OS can only be android or iOS')

        if self.os == 'ios':
            raise NotImplementedError('iOS is not supported at the moment.')
            # TODO: Support iOS

        self.mode = data['mode']

        if self.mode not in {'private', 'group'}:
            raise ValueError('Mode can only be either private or group.')

        self.warning = data['warning']
        self.size = tuple(data['size'])
        self.wallpaper_url = data['wallpaper']
        self.metadata = Metadata(self, data['metadata'])
        self.messages = [Message(self, i) for i in data['messages']]
        self.sorted_messages = sorted(self.messages, key=lambda x: x.timestamp)

        self.images = {}
        for i in os.listdir('images'):
            if i.endswith('.png'):
                self.images[i.replace('.png', '')] = Icon('images/' + i)

    def generate_wallpaper(self):
        if self.wallpaper_url:
            response = requests.get(self.wallpaper_url)
            img = Image.open(BytesIO(response.content)).convert('RGBA')
            img = img.resize(self.size, resample=Image.LANCZOS)
        else:
            # generate a default image
            img = Image.new('RGBA', self.size, Colors.BEIGE)
            bg_w, bg_h = img.size

            tile = self.images['wallpaper_tile'].generate_image()
            tile_w, tile_h = tile.size

            for x in range(0, bg_w, tile_w):
                for y in range(0, bg_h, tile_h):
                    img.alpha_composite(tile, (x, y))

        return img

    def generate_notification_bar(self):
        # draw.rectangle((0, 0, 720, 47), fill=(5, 76, 68))  # notification bar TODO: move it
        bar = Image.new('RGBA', (self.size[0], 50), color=Colors.DARK_GREEN)
        return bar

    def generate_top_bar(self):
        s_width = self.size[0]
        bar = Image.new('RGBA', (s_width, 110), color=Colors.GREEN)
        width, height = bar.size
        draw = ImageTextDraw(bar)

        img_size = height - 70
        # back_icon
        back_icon = self.images['back'].generate_image((img_size, img_size))
        bar.alpha_composite(back_icon, (10, 35))

        # group_icon
        icon_size = height - 40
        group_icon = self.metadata.generate_icon((icon_size, icon_size))
        bar.alpha_composite(group_icon, (60, 20))

        # subject
        draw.text((60 + icon_size + 10, 20), self.metadata.group_name, fill=Colors.WHITE, font=self.bold_font_35)
        draw.text((60 + icon_size + 10, 65), self.metadata.subtitle, fill=Colors.WHITE, font=self.font_25)

        # call (voice/video)
        if self.mode == 'private':
            video_call = self.images['video_call'].generate_image((img_size, img_size))
            bar.alpha_composite(video_call, (s_width - 250, 35))

            voice_call = self.images['voice_call'].generate_image((img_size, img_size))
            bar.alpha_composite(voice_call, (s_width - 155, 35))
        elif self.mode == 'group':
            group_call = self.images['group_call'].generate_image((img_size, img_size))
            bar.alpha_composite(group_call, (s_width - 155, 35))

        # more options
        more_options = self.images['more_options'].generate_image((img_size - 10, img_size - 10))
        bar.alpha_composite(more_options, (s_width - 65, 40))

        return bar

    def generate_bottom_bar(self):
        screen = self.generate_wallpaper()
        s_width, s_height = screen.size

        bar = screen.crop((0, s_height - 115, s_width, s_height))
        draw = ImageTextDraw(bar)
        b_width, b_height = bar.size
        draw.rounded_rectangle((10, 10, b_width - 110, b_height - 10), 50, Colors.WHITE)

        img_size = b_height - 10 - 10 - 50
        emoji = self.images['emoji'].generate_image((img_size, img_size))
        bar.alpha_composite(emoji, (30, 35))

        draw.text((30 + img_size + 20, 35), 'Type a message', fill=Colors.LIGHT_GREY, font=self.font_40)

        attach = self.images['attach'].generate_image((img_size, img_size))
        bar.alpha_composite(attach, (b_width - 110 - 160, 35))

        camera = self.images['camera'].generate_image((img_size, img_size))
        bar.alpha_composite(camera, (b_width - 110 - 70, 35))

        # size = 100
        draw.ellipse((b_width - 100, 10, b_width - 10, b_height - 10), fill=Colors.GREEN)

        mic = self.images['microphone'].generate_image((img_size, img_size))
        bar.alpha_composite(mic, (b_width - 77, 35))

        return bar


class Metadata:
    __slots__ = ('_conversation', 'group_name', 'icon_url', '_icon', 'last_seen', 'members', 'subtitle')

    def __init__(self, conversation, data):
        self._conversation = conversation
        self.group_name = data['name']
        self.icon_url = data['icon_url']
        self._icon = None

        self.last_seen = data['lastSeen']
        self.members = [Member(conversation, i) for i in data['members']]
        member_names = {i.name for i in self.members}

        if self._conversation.mode == 'private':
            # Data validation
            if len(self.members) > 2:
                raise ValueError(f'Mode has to be private for a conversation with more than 2 members. You have a conversation with {len(self.members)} members')

            for m in self.members:
                if not m.me:
                    self.group_name = m.name

        if sum(1 for m in self.members if m.me) != 1:
            raise ValueError('There has to be one member that is marked as "me"')

        self.subtitle = self.last_seen[:36] or ', '.join(member_names)[:36]

    def generate_icon(self, size):
        if self.icon_url:
            response = requests.get(self.icon_url)
            img = Image.open(BytesIO(response.content)).convert('RGBA')

            if img.size[0] != img.size[1]:
                # adjust to square
                smallest_xy = min(img.size[0], img.size[1])
                img.resize((smallest_xy, smallest_xy), resample=Image.LANCZOS)

            if size:
                img = img.resize(size, resample=Image.LANCZOS)
        else:
            if self._conversation.mode == 'private':
                icon = 'user_icon'
            elif self._conversation.mode == 'group':
                icon = 'group_icon'

            img = self._conversation.images[icon].generate_image(size)

        return img


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
        size, text_height, lines = get_text_size_box(530, self._conversation.font_35, self.cut_content, spacing=4)

        size = list(size)
        if not self.author.me and self._conversation.mode == 'group':
            # ensures that the name isnt too close to edge
            size[0] = max(size[0], self._conversation.bold_font_35.getsize(self.author.name)[0])

        size = [size[0] + 17 * 2, size[1] + 13 * 2]
        offset = 0
        if not self.author.me:
            if self._conversation.mode == 'group':
                size[1] += 50
                offset = 50
            color = Colors.OTHER
        else:
            color = Colors.SELF

        message = Image.new('RGBA', size, (0, 0, 0, 0))  # (255, 255, 255, 0)
        message_draw = ImageTextDraw(message)

        width, height = message.size

        # rounded rectangle
        message_draw.rounded_rectangle((0, 0, width, height), 15, fill=color)

        message_draw.text_box((17, 13 + offset), self.cut_content, (0, 0, 0), self._conversation.font_35, 530, spacing=4)

        if not self.author.me and self._conversation.mode == 'group':
            message_draw.text((17, 13), self.author.name, self.author.rgb_color, self._conversation.bold_font_35)

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
