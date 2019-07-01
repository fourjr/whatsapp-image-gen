# from models import Member, Message

__all__ = ('get_member', 'get_message')


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
