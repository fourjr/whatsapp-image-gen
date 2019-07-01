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
