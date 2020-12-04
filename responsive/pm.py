import json

import catbot
from responsive import blocked
from responsive import bot, config
from responsive import record_empty_test, command_detector


@blocked
def pass_on_cri(msg: catbot.Message) -> bool:
    return not msg.text.startswith('/') and msg.chat.type == 'private' and msg.chat.id != config['operator_id']


def pass_on(msg: catbot.Message):
    from_username = '@' + msg.from_.username if msg.from_.username != '' else 'No username'
    try:
        bot.send_message(chat_id=config['operator_id'],
                         text=config['messages']['pass_on_new_msg_to_op'].format(from_id=msg.from_.id,
                                                                                 from_name=msg.from_.name,
                                                                                 from_username=from_username),
                         parse_mode='HTML')
        bot.forward_message(from_chat_id=msg.chat.id, to_chat_id=config['operator_id'], msg_id=msg.id)
    except catbot.APIError:
        bot.send_message(chat_id=msg.from_.id, text=config['messages']['pass_on_sending_failed'])
        raise
    else:
        bot.send_message(chat_id=msg.from_.id, text=config['messages']['pass_on_sent_to_op_succ'])


def reply_cri(msg: catbot.Message) -> bool:
    return msg.text.startswith('/reply_') and msg.chat.id == config['operator_id']


def reply(msg: catbot.Message):
    if not msg.reply:
        bot.send_message(config['operator_id'], text=config['messages']['pass_on_reply_invalid'])
        return
    to_id = msg.text.split(' ')[0].split('_')[1]
    try:
        bot.send_message(chat_id=int(to_id), text=config['messages']['pass_on_reply_from_op'])
        bot.forward_message(from_chat_id=config['operator_id'], to_chat_id=int(to_id), msg_id=msg.reply_to_message.id)
    except catbot.ChatNotFoundError:
        bot.send_message(chat_id=config['operator_id'], text=config['messages']['pass_on_sending_failed'])
    except ValueError:
        bot.send_message(chat_id=config['operator_id'], text=config['messages']['pass_on_reply_invalid'])
    except catbot.APIError:
        bot.send_message(chat_id=config['operator_id'], text=config['messages']['pass_on_sending_failed'])
    else:
        bot.send_message(chat_id=config['operator_id'],
                         text=config['messages']['pass_on_reply_succ'].format(to_id=to_id))


def block_private_cri(msg: catbot.Message) -> bool:
    return command_detector('/block', msg) and msg.chat.id == config['operator_id']


def block_private(msg: catbot.Message):
    blocked_list, rec = record_empty_test('blocked', list)

    user_input_token = msg.text.split()
    id_to_block = []
    if len(user_input_token) == 1:
        bot.send_message(config['operator_id'], text=config['messages']['block_prompt'], reply_to_message_id=msg.id)
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
        bot.send_message(config['operator_id'], text=config['messages']['block_failed'], reply_to_message_id=msg.id)
    else:
        reply_text = config['messages']['block_succ']
        for item in delta:
            reply_text += str(item) + '\n'

        rec['blocked'] = list(blocked_set)
        json.dump(rec, open(config['record'], 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
        bot.send_message(config['operator_id'], text=reply_text, reply_to_message_id=msg.id)


def list_block_private_cri(msg: catbot.Message) -> bool:
    return command_detector('/list_blocked', msg) and msg.chat.id == config['operator_id']


def list_block_private(msg: catbot.Message):
    blocked_list = record_empty_test('blocked', list)[0]
    resp_text = ''
    if len(blocked_list) == 0:
        bot.send_message(config['operator_id'], text=config['messages']['list_block_empty'], reply_to_message_id=msg.id)
        return
    for item in blocked_list:
        resp_text += f'<a href="tg://user?id={item}">{item}</a>\n'

    bot.send_message(config['operator_id'], text=resp_text, parse_mode='HTML', reply_to_message_id=msg.id)


def unblock_private_cri(msg: catbot.Message) -> bool:
    return command_detector('/unblock', msg) and msg.chat.id == config['operator_id']


def unblock_private(msg: catbot.Message):
    blocked_list, rec = record_empty_test('blocked', list)

    user_input_token = msg.text.split()
    unblocked_id = []
    if len(user_input_token) == 1:
        bot.send_message(config['operator_id'], text=config['messages']['unblock_prompt'], reply_to_message_id=msg.id)
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
        bot.send_message(config['operator_id'], text=config['messages']['unblock_failed'], reply_to_message_id=msg.id)
    else:
        rec['blocked'] = blocked_list
        json.dump(rec, open(config['record'], 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
        resp_text = config['messages']['unblock_succ'] + '\n'.join(unblocked_id)
        bot.send_message(config['operator_id'], text=resp_text, reply_to_message_id=msg.id)
