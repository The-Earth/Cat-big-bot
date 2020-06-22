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


def get_chat_id_cri(msg: catbot.Message) -> bool:
    cmd = '/chat_id'
    return cmd in msg.commands or f'{cmd}@{bot.username}' in msg.commands


def get_chat_id(msg: catbot.Message):
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


def start_cri(msg: catbot.Message):
    cmd = '/start'
    return cmd in msg.commands and msg.chat.type == 'private'


def start(msg: catbot.Message):
    bot.send_message(chat_id=msg.chat.id, text='For private messaging with my operator, use /pass <message>.')


if __name__ == '__main__':
    bot.add_task(user_id_cri, user_id)
    bot.add_task(get_chat_id_cri, get_chat_id)
    bot.add_task(pass_on_cri, pass_on)
    bot.add_task(reply_cri, reply)
    bot.add_task(start_cri, start)

    while True:
        try:
            bot.start()
        except catbot.APIError as e:
            print(e.args[0])
