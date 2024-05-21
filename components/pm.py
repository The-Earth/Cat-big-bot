import catbot
from components.decorators import blocked
from components import bot

__all__ = [
    'pass_on',
    'reply',
    'block_private',
    'list_block_private',
    'unblock_private'
]


@blocked
def pass_on_cri(msg: catbot.Message) -> bool:
    return not msg.text.startswith('/') and msg.chat.type == 'private' and msg.chat.id != bot.config['operator_id']


@bot.msg_task(pass_on_cri)
def pass_on(msg: catbot.Message):
    from_username = '@' + msg.from_.username if msg.from_.username != '' else 'No username'
    try:
        bot.send_message(
            chat_id=bot.config['operator_id'],
            text=bot.config['messages']['pass_on_new_msg_to_op'].format(
                from_id=msg.from_.id,
                from_name=msg.from_.name,
                from_username=from_username
            ),
            parse_mode='HTML'
        )
        bot.forward_message(from_chat_id=msg.chat.id, to_chat_id=bot.config['operator_id'], msg_id=msg.id)
    except catbot.APIError:
        bot.send_message(chat_id=msg.from_.id, text=bot.config['messages']['pass_on_sending_failed'])
        raise
    else:
        bot.send_message(chat_id=msg.from_.id, text=bot.config['messages']['pass_on_sent_to_op_succ'])


def reply_cri(msg: catbot.Message) -> bool:
    return msg.text.startswith('/reply_') and msg.chat.id == bot.config['operator_id']


@bot.msg_task(reply_cri)
def reply(msg: catbot.Message):
    if not msg.reply:
        bot.send_message(bot.config['operator_id'], text=bot.config['messages']['pass_on_reply_invalid'])
        return
    to_id = msg.text.split(' ')[0].split('_')[1]
    try:
        bot.send_message(chat_id=int(to_id), text=bot.config['messages']['pass_on_reply_from_op'])
        bot.forward_message(from_chat_id=bot.config['operator_id'], to_chat_id=int(to_id), msg_id=msg.reply_to_message.id)
    except catbot.ChatNotFoundError:
        bot.send_message(chat_id=bot.config['operator_id'], text=bot.config['messages']['pass_on_sending_failed'])
    except ValueError:
        bot.send_message(chat_id=bot.config['operator_id'], text=bot.config['messages']['pass_on_reply_invalid'])
    except catbot.APIError:
        bot.send_message(chat_id=bot.config['operator_id'], text=bot.config['messages']['pass_on_sending_failed'])
    else:
        bot.send_message(
            chat_id=bot.config['operator_id'],
            text=bot.config['messages']['pass_on_reply_succ'].format(to_id=to_id)
        )


def block_private_cri(msg: catbot.Message) -> bool:
    return bot.detect_command('/block', msg) and msg.chat.id == bot.config['operator_id']


@bot.msg_task(block_private_cri)
def block_private(msg: catbot.Message):
    if 'blocked' in bot.record:
        blocked_list: list[int] = bot.record['blocked']
    else:
        blocked_list = []

    user_input_token = msg.text.split()
    id_to_block = []
    if len(user_input_token) == 1:
        bot.send_message(bot.config['operator_id'], text=bot.config['messages']['block_prompt'], reply_to_message_id=msg.id)
        return
    else:
        for item in user_input_token[1:]:
            try:
                id_to_block.append(int(item))
            except ValueError:
                continue

    blocked_set = set(blocked_list)
    old_blocked_set = blocked_set.copy()
    blocked_set.update(id_to_block)
    delta = blocked_set - old_blocked_set
    if len(delta) == 0:
        bot.send_message(
            bot.config['operator_id'],
            text=bot.config['messages']['block_failed'],
            reply_to_message_id=msg.id
        )
    else:
        reply_text = bot.config['messages']['block_succ']
        for item in delta:
            reply_text += str(item) + '\n'

        bot.record['blocked'] = list(blocked_set)
        bot.send_message(bot.config['operator_id'], text=reply_text, reply_to_message_id=msg.id)


def list_block_private_cri(msg: catbot.Message) -> bool:
    return bot.detect_command('/list_blocked', msg) and msg.chat.id == bot.config['operator_id']


@bot.msg_task(list_block_private_cri)
def list_block_private(msg: catbot.Message):
    if 'blocked' in bot.record:
        blocked_list: list[int] = bot.record['blocked']
    else:
        blocked_list = []
    resp_text = ''
    if len(blocked_list) == 0:
        bot.send_message(bot.config['operator_id'], text=bot.config['messages']['list_block_empty'], reply_to_message_id=msg.id)
        return
    for item in blocked_list:
        resp_text += f'<a href="tg://user?id={item}">{item}</a>\n'

    bot.send_message(bot.config['operator_id'], text=resp_text, parse_mode='HTML', reply_to_message_id=msg.id)


def unblock_private_cri(msg: catbot.Message) -> bool:
    return bot.detect_command('/unblock', msg) and msg.chat.id == bot.config['operator_id']


@bot.msg_task(unblock_private_cri)
def unblock_private(msg: catbot.Message):
    if 'blocked' in bot.record:
        blocked_list: list[int] = bot.record['blocked']
    else:
        blocked_list = []

    user_input_token = msg.text.split()
    unblocked_id = []
    if len(user_input_token) == 1:
        bot.send_message(bot.config['operator_id'], text=bot.config['messages']['unblock_prompt'], reply_to_message_id=msg.id)
        return
    else:
        for item in user_input_token[1:]:
            try:
                blocked_list.remove(int(item))
            except ValueError:
                continue
            else:
                unblocked_id.append(item)

    if len(unblocked_id) == 0:
        bot.send_message(bot.config['operator_id'], text=bot.config['messages']['unblock_failed'], reply_to_message_id=msg.id)
    else:
        bot.record['blocked'] = blocked_list
        resp_text = bot.config['messages']['unblock_succ'] + '\n'.join(unblocked_id)
        bot.send_message(bot.config['operator_id'], text=resp_text, reply_to_message_id=msg.id)
