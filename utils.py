# from models import Member, Message

__all__ = ('get_member', 'get_message', 'get_dimensions', 'get_text_size_box')


def get_member(conversation, member_id):  # -> Member:
    try:
        return next(m for m in conversation.metadata.members if m.id == member_id)
    except StopIteration as e:
        raise KeyError('Unable to find member') from e


def get_message(conversation, message_id):  # -> Message:
    try:
        return next(m for m in conversation.messages if m.id == message_id)
    except StopIteration as e:
        raise KeyError('Unable to find message') from e


def get_dimensions(name):
    # todo: fill this up when im less lazy
    dimensions = {
        'wallpaper': (),
        'attach': (45, 33),
        'back': (31, 33),
        'camera': (41, 39),
        'deleted': (),
        'star': (),
        'blue_tick': (32, 19),
        'double_tick': (32, 19),
        'single_tick': (),
        'emoji': (44, 40),
        'microphone': (30, 43),
        'more_options': (9, 32),
        'forward': (),
        'generic_doc': (),
        'doc_doc': (),
        'pdf_doc': (),
        'video_call': (41, 25),
        'voice_call': (38, 37),
        'group_call': (39, 37)
    }
    return dimensions[name]


def get_text_size_box(width, font, full_text, spacing):
    split = []
    x = 0
    y = 0

    for text in full_text.splitlines():
        lines = []
        line = []
        words = text.split()
        for word in words:
            new_line = ' '.join(line + [word])
            size = font.getsize(new_line)
            text_height = size[1] + 3
            if size[0] <= width:
                x = max(x, size[0])
                line.append(word)
            else:
                lines.append(line)
                line = [word]

        if line:
            lines.append(line)

        split.append([' '.join(line) for line in lines if line])
        y += text_height * len(split[-1]) + spacing

    return ((x, y), text_height, split)


class Colors:
    SELF = (220, 248, 198)
    OTHER = (255, 255, 255)
    WHITE = (255, 255, 255)
    LIGHT_GREY = (205, 205, 205)
    GREEN = (0, 136, 122)
