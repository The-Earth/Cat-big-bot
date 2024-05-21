import catbot
from components import bot
from components.decorators import trusted

__all__ = [
    'set_trusted',
    'list_trusted'
]


@trusted
def set_trusted_cri(msg: catbot.Message) -> bool:
    return bot.detect_command('/set_trusted', msg)


@bot.msg_task(set_trusted_cri)
def set_trusted(msg: catbot.Message):
    if 'trusted' in bot.record:
        trusted_list: list = bot.record['trusted']
    else:
        trusted_list = []

    new_trusted_id = []
    if msg.reply:
        new_trusted_id.append(msg.reply_to_message.from_.id)
    else:
        user_input_token = msg.text.split()
        if len(user_input_token) == 1:
            bot.send_message(msg.chat.id, text=bot.config['messages']['set_trusted_prompt'], reply_to_message_id=msg.id)
            return
        else:
            for item in user_input_token[1:]:
                try:
                    new_trusted_id.append(int(item))
                except ValueError:
                    continue

    trusted_set = set(trusted_list)
    old_trusted_set = trusted_set.copy()
    trusted_set.update(new_trusted_id)
    delta = trusted_set - old_trusted_set
    if len(delta) == 0:
        bot.send_message(msg.chat.id, text=bot.config['messages']['set_trusted_failed'], reply_to_message_id=msg.id)
    else:
        reply_text = bot.config['messages']['set_trusted_succ']
        for item in delta:
            reply_text += str(item) + '\n'

        bot.record['trusted'] = list(trusted_set)
        bot.send_message(msg.chat.id, text=reply_text, reply_to_message_id=msg.id)


@trusted
def list_trusted_cri(msg: catbot.Message) -> bool:
    return bot.detect_command('/list_trusted', msg) and msg.chat.type != 'private'


@bot.msg_task(list_trusted_cri)
def list_trusted(msg: catbot.Message):
    if 'trusted' in bot.record:
        trusted_list: list = bot.record['trusted']
    else:
        trusted_list = []

    resp_list = []
    bot.api('sendChatAction', {'chat_id': msg.chat.id, 'action': 'typing'})
    for trusted_id in trusted_list:
        try:
            trusted_user = bot.get_chat_member(msg.chat.id, trusted_id)
            if trusted_user.status == 'left' or trusted_user.status == 'kicked':
                continue
        except catbot.UserNotFoundError:
            continue
        else:
            resp_list.append(trusted_user)

    resp_text: str = bot.config['messages']['list_trusted_succ']
    for user in resp_list:
        resp_text += f'{user.name}、'
    resp_text = resp_text.rstrip('、')
    if len(resp_list) == 0:
        resp_text = bot.config['messages']['list_trusted_empty']

    bot.send_message(msg.chat.id, text=resp_text, reply_to_message_id=msg.id)
