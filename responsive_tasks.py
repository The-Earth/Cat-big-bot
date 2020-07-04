import json

import catbot

config = json.load(open('config.json', 'r', encoding='utf-8'))

bot = catbot.Bot(config)


def command_detector(cmd: str, msg: catbot.Message) -> bool:
    if cmd in msg.commands:
        return msg.text.startswith(cmd)
    elif f'{cmd}@{bot.username}' in msg.commands:
        return msg.text.startswith(f'{cmd}@{bot.username}')


def get_user_id_cri(msg: catbot.Message) -> bool:
    return command_detector('/user_id', msg)


def get_user_id(msg: catbot.Message):
    from_id = msg.from_.id
    chat_id = msg.chat.id
    reply_to = msg.id
    bot.send_message(text=from_id, chat_id=chat_id, reply_to_message_id=reply_to)


def get_chat_id_cri(msg: catbot.Message) -> bool:
    return command_detector('/chat_id', msg)


def get_chat_id(msg: catbot.Message):
    chat_id = msg.chat.id
    reply_to = msg.id
    bot.send_message(text=chat_id, chat_id=chat_id, reply_to_message_id=reply_to)


def pass_on_cri(msg: catbot.Message) -> bool:
    return command_detector('/pass', msg) and msg.chat.type == 'private'


def pass_on(msg: catbot.Message):
    from_id = msg.from_.id
    from_username = '@' + msg.from_.username if msg.from_.username != '' else 'No username'
    from_name = msg.from_.name
    text = msg.text.lstrip('/pass ')
    try:
        bot.send_message(chat_id=config['operator_id'],
                         text=config['messages']['pass_on_new_msg_to_op'].format(from_id=from_id, from_name=from_name,
                                                                                 from_username=from_username,
                                                                                 text=text),
                         parse_mode='HTML')
    except catbot.APIError:
        bot.send_message(chat_id=from_id, text=config['messages']['pass_on_sending_failed'])
        raise
    finally:
        bot.send_message(chat_id=from_id, text=config['messages']['pass_on_sent_to_op_succ'])


def reply_cri(msg: catbot.Message) -> bool:
    chat_id = msg.chat.id
    return command_detector('/reply', msg) and chat_id == config['operator_id']


def reply(msg: catbot.Message):
    text = msg.text.lstrip('/reply ')
    to_id = text.split(' ')[0]
    content = ' '.join(text.split(' ')[1:])
    try:
        bot.send_message(chat_id=to_id, text=config['messages']['pass_on_reply_from_op'].format(content=content))
    except catbot.APIError as ex:
        if 'chat not found' in ex.args[0]:
            bot.send_message(chat_id=config['operator_id'],
                             text=config['messages']['pass_on_reply_invalid_id'])
        else:
            bot.send_message(chat_id=config['operator_id'], text=config['messages']['pass_on_sending_failed'])
            raise
    else:
        bot.send_message(chat_id=config['operator_id'],
                         text=config['messages']['pass_on_reply_succ'].format(to_id=to_id))


def start_cri(msg: catbot.Message) -> bool:
    return command_detector('/start', msg) and msg.chat.type == 'private'


def start(msg: catbot.Message):
    bot.send_message(chat_id=msg.chat.id, text=config['messages']['start'])


def mark_cri(msg: catbot.Message) -> bool:
    return command_detector('/mark', msg)


def mark(msg: catbot.Message, rec_file: str):
    mark_rec = json.load(open(rec_file, 'r', encoding='utf-8'))
    msg_id = msg.id
    chat_id = msg.chat.id
    chat_link = msg.chat.link
    if chat_link == '':
        bot.send_message(chat_id, text=config['messages']['mark_private'], reply_to_message_id=msg_id)
        return
    if not msg.reply:
        bot.send_message(chat_id, text=config['messages']['mark_empty_reply'], reply_to_message_id=msg_id)
        return
    reply_to_id = msg.reply_to_message.id

    comment = msg.text.lstrip('/mark')

    if str(chat_id) not in mark_rec.keys():
        mark_rec[str(chat_id)] = [{'id': reply_to_id, 'comment': comment}]
    else:
        mark_rec[str(chat_id)].append({'id': reply_to_id, 'comment': comment})
    json.dump(mark_rec, open(rec_file, 'w', encoding='utf-8'), indent=2)
    bot.send_message(chat_id, text=config['messages']['mark_succ'], reply_to_message_id=msg_id)


def list_marked_cri(msg: catbot.Message) -> bool:
    return command_detector('/list_marked', msg)


def list_marked(msg: catbot.Message, rec_file: str):
    mark_rec = json.load(open(rec_file, 'r', encoding='utf-8'))
    msg_id = msg.id
    chat_id: int = msg.chat.id
    chat_link = msg.chat.link

    if chat_link == '':
        bot.send_message(chat_id, text=config['messages']['mark_private'], reply_to_message_id=msg_id)
        return

    if str(chat_id) not in mark_rec.keys() or len(mark_rec[str(chat_id)]) == 0:
        bot.send_message(chat_id, text=config['messages']['mark_list_empty'], reply_to_message_id=msg_id)
    else:
        text = ''
        for record in mark_rec[str(chat_id)]:
            text += f'{chat_link}/{record["id"]} {record["comment"]}\n'
        bot.send_message(chat_id, text=text, reply_to_message_id=msg_id, disable_web_page_preview=True)


def unmark_cri(msg: catbot.Message) -> bool:
    return command_detector('/unmark', msg)


def unmark(msg: catbot.Message, rec_file: str):
    mark_rec = json.load(open(rec_file, 'r', encoding='utf-8'))
    msg_id = msg.id
    chat_id = msg.chat.id
    chat_link = msg.chat.link
    if chat_link == '':
        bot.send_message(chat_id, text=config['messages']['mark_private'], reply_to_message_id=msg_id)
        return
    if str(chat_id) not in mark_rec.keys() or len(mark_rec[str(chat_id)]) == 0:
        bot.send_message(chat_id, text=config['messages']['mark_list_empty'], reply_to_message_id=msg_id)
        return

    unmark_list = []
    if msg.reply:
        unmark_list.append(msg.reply_to_message.id)
    else:
        user_input_token = msg.text.split()
        if len(user_input_token) == 1:
            bot.send_message(chat_id, text=config['messages']['mark_unmark_prompt'], reply_to_message_id=msg_id)
            return
        else:
            for item in user_input_token[1:]:
                try:
                    unmark_list.append(int(item))
                except ValueError:
                    continue

    response_text = config['messages']['mark_unmark_succ']
    i = 0
    while i < len(mark_rec[str(chat_id)]):
        if mark_rec[str(chat_id)][i]['id'] in unmark_list:
            unmarked_id = mark_rec[str(chat_id)][i]['id']
            mark_rec[str(chat_id)].pop(i)
            json.dump(mark_rec, open(rec_file, 'w', encoding='utf-8'), indent=2)
            response_text += str(unmarked_id) + '\n'
        else:
            i += 1

    if response_text != config['messages']['mark_unmark_succ']:
        bot.send_message(chat_id, text=response_text, reply_to_message_id=msg_id)
    else:
        bot.send_message(chat_id, text=config['messages']['mark_unmark_failed'], reply_to_message_id=msg_id)


if __name__ == '__main__':
    bot.add_task(get_user_id_cri, get_user_id)
    bot.add_task(get_chat_id_cri, get_chat_id)
    bot.add_task(pass_on_cri, pass_on)
    bot.add_task(reply_cri, reply)
    bot.add_task(start_cri, start)
    bot.add_task(mark_cri, mark, rec_file=config['mark_rec'])
    bot.add_task(list_marked_cri, list_marked, rec_file=config['mark_rec'])
    bot.add_task(unmark_cri, unmark, rec_file=config['mark_rec'])

    while True:
        try:
            bot.start()
        except catbot.APIError as e:
            print(e.args[0])
