import json

import catbot

from responsive import trusted
from responsive import bot, config, t_lock
from responsive import command_detector, record_empty_test


@trusted
def set_channel_helper_cri(msg: catbot.Message) -> bool:
    return command_detector('/set_channel_helper', msg) and msg.chat.type == 'supergroup'


def set_channel_helper(msg: catbot.Message):
    with t_lock:
        helper_set, rec = record_empty_test('channel_helper', list)
        helper_set.append(msg.chat.id)
        rec['channel_helper'] = helper_set
        json.dump(rec, open(config['record'], 'w', encoding='utf-8'), indent=2, ensure_ascii=False)

    bot.send_message(msg.chat.id, text=config['messages']['set_channel_helper_succ'], reply_to_message_id=msg.id)


def channel_helper_cri(msg: catbot.ChatMemberUpdate) -> bool:
    if msg.old_chat_member.status == 'left' and msg.new_chat_member.status == 'member':
        return True
    elif msg.old_chat_member.status == msg.new_chat_member.status == 'restricted':
        return not msg.old_chat_member.is_member and msg.new_chat_member.is_member
    else:
        return False


def channel_helper(msg: catbot.ChatMemberUpdate):
    with t_lock:
        helper_set, rec = record_empty_test('channel_helper', list)

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


def channel_helper_msg_deletion(msg: catbot.Message):
    with t_lock:
        helper_set, rec = record_empty_test('channel_helper', list)

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
    return command_detector('/unset_channel_helper', msg) and msg.chat.type == 'supergroup'


def unset_channel_helper(msg: catbot.Message):
    with t_lock:
        helper_set, rec = record_empty_test('channel_helper', list)
        if msg.chat.id in helper_set:
            helper_set.remove(msg.chat.id)
        rec['channel_helper'] = helper_set
        json.dump(rec, open(config['record'], 'w', encoding='utf-8'), indent=2, ensure_ascii=False)

    bot.send_message(msg.chat.id, text=config['messages']['unset_channel_helper_succ'], reply_to_message_id=msg.id)
