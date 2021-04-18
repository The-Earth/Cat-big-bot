import json

import catbot

from responsive import admin
from responsive import bot, config, t_lock
from responsive import command_detector, record_empty_test

@admin
def set_channel_helper_cri(msg: catbot.Message) -> bool:
    return command_detector('/set_channel_helper', msg) and msg.chat.type == 'supergroup'


def set_channel_helper(msg: catbot.Message):
    with t_lock:
        helper_set, rec = record_empty_test('channel_helper', list)
        helper_set.append(msg.chat.id)
        rec['channel_helper'] = helper_set
        json.dump(rec, open(config['record'], 'w', encoding='utf-8'), indent=2, ensure_ascii=False)

    bot.send_message(msg.chat.id, text=config['messages']['set_channel_helper_succ'], reply_to_message_id=msg.id)


def channel_helper_cri(msg: catbot.Message) -> bool:
    return hasattr(msg, 'new_chat_members')


def channel_helper(msg: catbot.Message):
    with t_lock:
        helper_set, rec = record_empty_test('channel_helper', list)

    if msg.chat.id not in helper_set:
        return

    for new_member in msg.new_chat_members:
        if new_member.id == msg.from_.id:
            try:
                bot.kick_chat_member(msg.chat.id, new_member.id, no_ban=True)
                bot.delete_message(msg.chat.id, msg.id)
            except catbot.InsufficientRightError:
                pass
            except catbot.UserNotFoundError:
                pass
            except catbot.RestrictAdminError:
                pass
            except catbot.DeleteMessageError:
                pass


def channel_helper_left_msg_deletion_cri(msg: catbot.Message) -> bool:
    return hasattr(msg, 'left_chat_member') and msg.from_.id == bot.id


def channel_helper_left_msg_deletion(msg: catbot.Message):
    with t_lock:
        helper_set, rec = record_empty_test('channel_helper', list)

    if msg.chat.id not in helper_set:
        return

    try:
        bot.delete_message(msg.chat.id, msg.id)
    except catbot.InsufficientRightError:
        pass
    except catbot.DeleteMessageError:
        pass


@admin
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
