import json

import catbot

from responsive import trusted
from responsive import bot, config, t_lock


@trusted
def set_show_joining_cri(msg: catbot.Message) -> bool:
    return bot.detect_command('/show_joining', msg) and msg.chat.type == 'supergroup'


def set_show_joining(msg: catbot.Message):
    with t_lock:
        show_joining_set, rec = bot.secure_record_fetch('show_joining', list)
        show_joining_set.append(msg.chat.id)
        rec['show_joining'] = show_joining_set
        json.dump(rec, open(config['record'], 'w', encoding='utf-8'), indent=2, ensure_ascii=False)

    bot.send_message(msg.chat.id, text=config['messages']['set_show_joining_succ'], reply_to_message_id=msg.id)


def show_joining_cri(msg: catbot.ChatMemberUpdate) -> bool:
    if msg.old_chat_member.status == 'left' and msg.new_chat_member.status == 'member':
        return True
    elif msg.old_chat_member.status == msg.new_chat_member.status == 'restricted':
        return not msg.old_chat_member.is_member and msg.new_chat_member.is_member
    else:
        return False


def show_joining(msg: catbot.ChatMemberUpdate):
    with t_lock:
        show_joining_set, rec = bot.secure_record_fetch('show_joining', list)

    if msg.chat.id not in show_joining_set:
        return

    bot.send_message(msg.chat.id,
                     text=config['messages']['show_joining'].format(user_id=msg.new_chat_member.id,
                                                                                 user_name=msg.new_chat_member.name),
                     parse_mode='HTML')


@trusted
def unset_show_joining_cri(msg: catbot.Message) -> bool:
    return bot.detect_command('/hide_joining', msg) and msg.chat.type == 'supergroup'


def unset_show_joining(msg: catbot.Message):
    with t_lock:
        helper_set, rec = bot.secure_record_fetch('show_joining', list)
        if msg.chat.id in helper_set:
            helper_set.remove(msg.chat.id)
        rec['show_joining'] = helper_set
        json.dump(rec, open(config['record'], 'w', encoding='utf-8'), indent=2, ensure_ascii=False)

    bot.send_message(msg.chat.id, text=config['messages']['unset_show_joining_succ'], reply_to_message_id=msg.id)
