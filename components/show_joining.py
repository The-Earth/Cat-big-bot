import catbot

from components.decorators import trusted
from components import bot, t_lock

__all__ = [
    'show_joining',
    'set_show_joining',
    'unset_show_joining'
]


@trusted
def set_show_joining_cri(msg: catbot.Message) -> bool:
    return bot.detect_command('/show_joining', msg) and msg.chat.type == 'supergroup'


@bot.msg_task(set_show_joining_cri)
def set_show_joining(msg: catbot.Message):
    with t_lock:
        if 'show_joining' in bot.record:
            show_joining_list: list = bot.record['show_joining']
        else:
            show_joining_list = []
        show_joining_set = set(show_joining_list)
        show_joining_set.add(msg.chat.id)
        show_joining_list = list(show_joining_set)
        bot.record['show_joining'] = show_joining_list

    bot.send_message(msg.chat.id, text=bot.config['messages']['set_show_joining_succ'], reply_to_message_id=msg.id)


def show_joining_cri(msg: catbot.ChatMemberUpdate) -> bool:
    if msg.old_chat_member.status == 'left' and msg.new_chat_member.status == 'member':
        return True
    elif msg.old_chat_member.status == msg.new_chat_member.status == 'restricted':
        return not msg.old_chat_member.is_member and msg.new_chat_member.is_member
    else:
        return False


@bot.member_status_task(show_joining_cri)
def show_joining(msg: catbot.ChatMemberUpdate):
    with t_lock:
        if 'show_joining' in bot.record:
            show_joining_list: list = bot.record['show_joining']
        else:
            show_joining_list = []

    if msg.chat.id not in show_joining_list:
        return

    bot.send_message(
        msg.chat.id,
        text=bot.config['messages']['show_joining'].format(
            user_id=msg.new_chat_member.id,
            user_name=msg.new_chat_member.name
        ),
        parse_mode='HTML'
    )


@trusted
def unset_show_joining_cri(msg: catbot.Message) -> bool:
    return bot.detect_command('/hide_joining', msg) and msg.chat.type == 'supergroup'


@bot.msg_task(unset_show_joining_cri)
def unset_show_joining(msg: catbot.Message):
    with t_lock:
        if 'show_joining' in bot.record:
            show_joining_list: list = bot.record['show_joining']
        else:
            show_joining_list = []
        if msg.chat.id in show_joining_list:
            show_joining_list.remove(msg.chat.id)
        bot.record['show_joining'] = show_joining_list

    bot.send_message(msg.chat.id, text=bot.config['messages']['unset_show_joining_succ'], reply_to_message_id=msg.id)
