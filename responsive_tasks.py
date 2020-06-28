import json

import catbot

config = json.load(open('config.json', 'r', encoding='utf-8'))

bot = catbot.Bot(config)


def user_id_cri(msg: catbot.Message) -> bool:
    cmd = '/user_id'
    return cmd in msg.commands or f'{cmd}@{bot.username}' in msg.commands


def user_id(msg: catbot.Message):
    from_id = msg.from_.id
    chat_id = msg.chat.id
    reply_to = msg.id
    bot.send_message(text=from_id, chat_id=chat_id, reply_to_message_id=reply_to)


def chat_id_cri(msg: catbot.Message) -> bool:
    cmd = '/chat_id'
    return cmd in msg.commands or f'{cmd}@{bot.username}' in msg.commands


def chat_id(msg: catbot.Message):
    chat_id = msg.chat.id
    reply_to = msg.id
    bot.send_message(text=chat_id, chat_id=chat_id, reply_to_message_id=reply_to)


def pass_on_cri(msg: catbot.Message) -> bool:
    cmd = '/pass'
    return cmd in msg.commands and msg.chat.type == 'private'


def pass_on(msg: catbot.Message):
    from_id = msg.from_.id
    from_username = '@' + msg.from_.username if msg.from_.username != '' else 'No username'
    from_name = msg.from_.name
    text = msg.text.lstrip('/pass ')
    try:
        bot.send_message(chat_id=config['operator_id'],
                         text=f'Received PM from <a href="tg://user?id={from_id}">{from_name}</a> (ID: {from_id}, '
                              f'{from_username})\n----\n{text}',
                         parse_mode='HTML')
    except catbot.APIError:
        bot.send_message(chat_id=from_id, text='Sending failed. Please retry later.')
        raise
    finally:
        bot.send_message(chat_id=from_id, text='Message sent to operator.')


def reply_cri(msg: catbot.Message) -> bool:
    cmd = '/reply'
    chat_id = msg.chat.id
    return cmd in msg.commands and chat_id == config['operator_id']


def reply(msg: catbot.Message):
    text = msg.text.lstrip('/reply ')
    to_id = text.split(' ')[0]
    content = ' '.join(text.split(' ')[1:])
    try:
        bot.send_message(chat_id=to_id, text='Reply from operator:\n' + content)
    except catbot.APIError as e:
        if 'chat not found' in e.args[0]:
            bot.send_message(chat_id=config['operator_id'],
                             text='User id invalid. Reply format: /reply <user id> <text>')
        else:
            bot.send_message(chat_id=config['operator_id'], text='Sending failed.')
            raise


def start_cri(msg: catbot.Message) -> bool:
    cmd = '/start'
    return cmd in msg.commands and msg.chat.type == 'private'


def start(msg: catbot.Message):
    bot.send_message(chat_id=msg.chat.id, text='For private messaging with my operator, use /pass <message>.')


def mark_cri(msg: catbot.Message) -> bool:
    cmd = '/mark'
    return cmd in msg.commands or f'{cmd}@{bot.username}' in msg.commands


def mark(msg: catbot.Message, rec_file: str):
    mark_rec = json.load(open(rec_file, 'r', encoding='utf-8'))
    msg_id = msg.id
    chat_id = msg.chat.id
    chat_link = msg.chat.link
    if chat_link == '':
        bot.send_message(chat_id, text='/mark supports groups only.', reply_to_message_id=msg_id)
        return
    if not msg.reply:
        bot.send_message(chat_id, text='Reply the message you want to mark with /mark.', reply_to_message_id=msg_id)
        return
    reply_to_id = msg.reply_to_message.id

    comment = msg.text.lstrip('/mark')

    if str(chat_id) not in mark_rec.keys():
        mark_rec[str(chat_id)] = [{'id': reply_to_id, 'comment': comment}]
    else:
        mark_rec[str(chat_id)].append({'id': reply_to_id, 'comment': comment})
    json.dump(mark_rec, open(rec_file, 'w', encoding='utf-8'), indent=2)
    bot.send_message(chat_id, text='Marked.', reply_to_message_id=msg_id)


def list_marked_cri(msg: catbot.Message) -> bool:
    cmd = '/list_marked'
    return cmd in msg.commands or f'{cmd}@{bot.username}' in msg.commands


def list_marked(msg: catbot.Message, rec_file: str):
    mark_rec = json.load(open(rec_file, 'r', encoding='utf-8'))
    msg_id = msg.id
    chat_id: int = msg.chat.id
    chat_link = msg.chat.link

    if chat_link == '':
        bot.send_message(chat_id, text='/list_marked supports groups only.', reply_to_message_id=msg_id)
        return

    if str(chat_id) not in mark_rec.keys() or len(mark_rec[str(chat_id)]) == 0:
        bot.send_message(chat_id, text='No marks found.', reply_to_message_id=msg_id)
    else:
        text = ''
        for record in mark_rec[str(chat_id)]:
            text += f'{chat_link}/{record["id"]} {record["comment"]}\n'
        bot.send_message(chat_id, text=text, reply_to_message_id=msg_id, disable_web_page_preview=True)


def unmark_cri(msg: catbot.Message) -> bool:
    cmd = '/unmark'
    return cmd in msg.commands or f'{cmd}@{bot.username}' in msg.commands


def unmark(msg:catbot.Message, rec_file: str):
    mark_rec = json.load(open(rec_file, 'r', encoding='utf-8'))
    msg_id = msg.id
    chat_id = msg.chat.id
    chat_link = msg.chat.link
    if chat_link == '':
        bot.send_message(chat_id, text='/unmark supports groups only.', reply_to_message_id=msg_id)
        return

    unmark_list = []
    if msg.reply:
        unmark_list.append(msg.reply_to_message.id)
    else:
        user_input_token = msg.text.split()
        if len(user_input_token) == 1:
            bot.send_message(chat_id, text='Reply the message you want to unmark with /unmark or use'
                                           ' "/unmark <message id>" to unmark.', reply_to_message_id=msg_id)
            return
        else:
            for item in user_input_token[1:]:
                try:
                    unmark_list.append(int(item))
                except ValueError:
                    bot.send_message(chat_id, text='Problematic message id, check it.')
                    continue

    response_text = 'Unmarked:\n'
    i = 0
    while i < len(mark_rec[str(chat_id)]):
        if mark_rec[str(chat_id)][i]['id'] in unmark_list:
            unmarked_id = mark_rec[str(chat_id)][i]['id']
            mark_rec[str(chat_id)].pop(i)
            json.dump(mark_rec, open(rec_file, 'w', encoding='utf-8'), indent=2)
            response_text += str(unmarked_id) + '\n'
        else:
            i += 1

    if response_text != 'Unmarked:\n':
        bot.send_message(chat_id, text=response_text, reply_to_message_id=msg_id)
    else:
        bot.send_message(chat_id, text='Selected messages are not marked.')


if __name__ == '__main__':
    bot.add_task(user_id_cri, user_id)
    bot.add_task(chat_id_cri, chat_id)
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
