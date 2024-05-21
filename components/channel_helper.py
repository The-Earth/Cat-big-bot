import catbot

from components.decorators import trusted
from components import bot, t_lock

__all__ = [
    'set_channel_helper',
    'channel_helper',
    'channel_helper_msg_deletion',
    'unset_channel_helper'
]


@trusted
def set_channel_helper_cri(msg: catbot.Message) -> bool:
    return bot.detect_command('/set_channel_helper', msg) and msg.chat.type == 'supergroup'


@bot.msg_task(set_channel_helper_cri)
def set_channel_helper(msg: catbot.Message):
    with t_lock:
        if 'channel_helper' in bot.record:
            helper_set: list[int] = bot.record['channel_helper']
        else:
            helper_set = []
        helper_set.append(msg.chat.id)
        bot.record['channel_helper'] = helper_set

    bot.send_message(msg.chat.id, text=bot.config['messages']['set_channel_helper_succ'], reply_to_message_id=msg.id)


def channel_helper_cri(msg: catbot.ChatMemberUpdate) -> bool:
    if msg.old_chat_member.status == 'left' and msg.new_chat_member.status == 'member':
        return True
    elif msg.old_chat_member.status == msg.new_chat_member.status == 'restricted':
        return not msg.old_chat_member.is_member and msg.new_chat_member.is_member
    else:
        return False


@bot.member_status_task(channel_helper_cri)
def channel_helper(msg: catbot.ChatMemberUpdate):
    with t_lock:
        if 'channel_helper' in bot.record:
            helper_set = bot.record['channel_helper']
        else:
            helper_set = []

    if msg.chat.id not in helper_set:
        return

    if msg.from_.id != msg.new_chat_member.id:
        return

    try:
        bot.kick_chat_member(msg.chat.id, msg.new_chat_member.id, no_ban=True)
    except catbot.InsufficientRightError:
        pass
    except catbot.UserNotFoundError:
        pass
    except catbot.RestrictAdminError:
        pass


def channel_helper_msg_deletion_cri(msg: catbot.Message) -> bool:
    return hasattr(msg, 'left_chat_member') or hasattr(msg, 'new_chat_members')


@bot.msg_task(channel_helper_msg_deletion_cri)
def channel_helper_msg_deletion(msg: catbot.Message):
    with t_lock:
        if 'channel_helper' in bot.record:
            helper_set: list[int] = bot.record['channel_helper']
        else:
            helper_set = []

    if msg.chat.id not in helper_set:
        return

    if hasattr(msg, 'left_chat_member') and msg.from_.id != bot.id:
        return

    if hasattr(msg, 'new_chat_members') and msg.new_chat_members[0].id != msg.from_.id:
        return

    try:
        bot.delete_message(msg.chat.id, msg.id)
    except catbot.InsufficientRightError:
        pass
    except catbot.DeleteMessageError:
        pass


@trusted
def unset_channel_helper_cri(msg: catbot.Message) -> bool:
    return bot.detect_command('/unset_channel_helper', msg) and msg.chat.type == 'supergroup'


@bot.msg_task(unset_channel_helper_cri)
def unset_channel_helper(msg: catbot.Message):
    with t_lock:
        if 'channel_helper' in bot.record:
            helper_set: list[int] = bot.record['channel_helper']
        else:
            helper_set = []
        helper_set.remove(msg.chat.id)
        bot.record['channel_helper'] = helper_set

    bot.send_message(msg.chat.id, text=bot.config['messages']['unset_channel_helper_succ'], reply_to_message_id=msg.id)
