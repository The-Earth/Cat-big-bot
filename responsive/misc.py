import json

import catbot

from responsive import admin
from responsive import bot, config, t_lock
from responsive import command_detector, record_empty_test


def get_user_id_cri(msg: catbot.Message) -> bool:
    return command_detector('/user_id', msg)


def get_user_id(msg: catbot.Message):
    if msg.reply:
        res_id = msg.reply_to_message.from_.id
    else:
        res_id = msg.from_.id
    bot.send_message(chat_id=msg.chat.id, text=res_id, reply_to_message_id=msg.id)


def get_chat_id_cri(msg: catbot.Message) -> bool:
    return command_detector('/chat_id', msg)


def get_chat_id(msg: catbot.Message):
    bot.send_message(chat_id=msg.chat.id, text=msg.chat.id, reply_to_message_id=msg.id)


def start_cri(msg: catbot.Message) -> bool:
    return command_detector('/start', msg) and msg.chat.type == 'private'


def start(msg: catbot.Message):
    bot.send_message(chat_id=msg.chat.id, text=config['messages']['start'])


def bot_help_cri(msg: catbot.Message) -> bool:
    if msg.chat.type != 'private':
        return f'/help@{bot.username}' in msg.commands and msg.text.startswith(f'/help@{bot.username}')
    else:
        return command_detector('/help', msg)


def bot_help(msg: catbot.Message):
    bot.send_message(msg.chat.id, text=config['messages']['help'], reply_to_message_id=msg.id)


def get_permalink_cri(msg: catbot.Message) -> bool:
    return command_detector('/permalink', msg) and msg.chat.type == 'private'


def get_permalink(msg: catbot.Message):
    id_list = []
    user_input_token = msg.text.split()
    if len(user_input_token) == 1:
        bot.send_message(msg.chat.id, text=config['messages']['permalink_prompt'], reply_to_message_id=msg.id)
        return
    else:
        for item in user_input_token[1:]:
            try:
                id_list.append(int(item))
            except ValueError:
                continue

    resp_text = ''
    for item in id_list:
        resp_text += f'<a href="tg://user?id={item}">{item}</a>\n'
    bot.send_message(msg.chat.id, text=resp_text, parse_mode='HTML', reply_to_message_id=msg.id)


@admin
def set_channel_helper_cri(msg: catbot.Message) -> bool:
    return command_detector('/set_channel_helper', msg) and msg.chat.type == 'supergroup'


def set_channel_helper(msg: catbot.Message):
    with t_lock:
        helper_set, rec = record_empty_test('channel_helper', set)
        helper_set.add(msg.chat.id)
        rec['channel_helper'] = helper_set
        json.dump(rec, open(config['record'], 'w', encoding='utf-8'), indent=2, ensure_ascii=False)

    bot.send_message(msg.chat.id, text=config['messages']['set_channel_helper_succ'], reply_to_message_id=msg.id)


def channel_helper_cri(msg: catbot.Message) -> bool:
    return hasattr(msg, 'new_chat_members')


def channel_helper(msg: catbot.Message):
    with t_lock:
        helper_set, rec = record_empty_test('channel_helper', set)

    if msg.chat.id not in helper_set:
        return

    for new_member in msg.new_chat_members:
        if new_member.id == msg.from_.id:
            try:
                bot.api('unbanChatMember', {'chat_id': msg.chat.id, 'user_id': new_member.id})
                bot.api('deleteMessage', {'chat_id': msg.chat.id, 'message_id': msg.id})
            except catbot.InsufficientRightError:
                pass
            except catbot.UserNotFoundError:
                pass
            except catbot.RestrictAdminError:
                pass


@admin
def unset_channel_helper_cri(msg: catbot.Message) -> bool:
    return command_detector('/unset_channel_helper', msg) and msg.chat.type == 'supergroup'


def unset_channel_helper(msg: catbot.Message):
    with t_lock:
        helper_set, rec = record_empty_test('channel_helper', set)
        if msg.chat.id in helper_set:
            helper_set.remove(msg.chat.id)
        rec['channel_helper'] = helper_set
        json.dump(rec, open(config['record'], 'w', encoding='utf-8'), indent=2, ensure_ascii=False)

    bot.send_message(msg.chat.id, text=config['messages']['unset_channel_helper_succ'], reply_to_message_id=msg.id)
