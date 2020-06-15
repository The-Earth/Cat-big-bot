import json
import catbot

config = json.load(open('config.json', 'r', encoding='utf-8'))

bot = catbot.Bot(config)


def get_id_cri(msg: catbot.Message) -> bool:
    return '/user_id' in msg.commands


def get_id(msg: catbot.Message):
    from_id = msg.from_.id
    chat_id = msg.chat.id
    reply_to = msg.id
    bot.send_message(text=from_id, chat_id=chat_id, reply_to_message_id=reply_to)


def get_chat_id_cri(msg: catbot.Message) -> bool:
    return '/chat_id' in msg.commands


def get_chat_id(msg: catbot.Message):
    chat_id = msg.chat.id
    reply_to = msg.id
    bot.send_message(text=chat_id, chat_id=chat_id, reply_to_message_id=reply_to)


if __name__ == '__main__':
    bot.add_task(get_id_cri, get_id)
    bot.add_task(get_chat_id_cri, get_chat_id)

    bot.start()
