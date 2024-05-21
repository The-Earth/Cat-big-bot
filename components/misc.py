import catbot

from components import bot

__all__ = [
    'get_user_id',
    'get_chat_id',
    'start',
    'bot_help',
    'get_permalink',
    'raw_api'
]


def get_user_id_cri(msg: catbot.Message) -> bool:
    return bot.detect_command('/user_id', msg)


@bot.msg_task(get_user_id_cri)
def get_user_id(msg: catbot.Message):
    if msg.reply:
        res_id = msg.reply_to_message.from_.id
    else:
        res_id = msg.from_.id
    bot.send_message(chat_id=msg.chat.id, text=str(res_id), reply_to_message_id=msg.id)


def get_chat_id_cri(msg: catbot.Message) -> bool:
    return bot.detect_command('/chat_id', msg)


@bot.msg_task(get_chat_id_cri)
def get_chat_id(msg: catbot.Message):
    bot.send_message(chat_id=msg.chat.id, text=str(msg.chat.id), reply_to_message_id=msg.id)


def start_cri(msg: catbot.Message) -> bool:
    return bot.detect_command('/start', msg) and msg.chat.type == 'private'


@bot.msg_task(start_cri)
def start(msg: catbot.Message):
    bot.send_message(chat_id=msg.chat.id, text=bot.config['messages']['start'])


def bot_help_cri(msg: catbot.Message) -> bool:
    if msg.chat.type != 'private':
        return f'/help@{bot.username}' in msg.commands and msg.text.startswith(f'/help@{bot.username}')
    else:
        return bot.detect_command('/help', msg)


@bot.msg_task(bot_help_cri)
def bot_help(msg: catbot.Message):
    bot.send_message(msg.chat.id, text=bot.config['messages']['help'], reply_to_message_id=msg.id)


def get_permalink_cri(msg: catbot.Message) -> bool:
    return bot.detect_command('/permalink', msg) and msg.chat.type == 'private'


@bot.msg_task(get_permalink_cri)
def get_permalink(msg: catbot.Message):
    id_list = []
    user_input_token = msg.text.split()
    if len(user_input_token) == 1:
        bot.send_message(msg.chat.id, text=bot.config['messages']['permalink_prompt'], reply_to_message_id=msg.id)
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


def raw_api_cri(msg: catbot.Message) -> bool:
    return bot.detect_command('/api', msg) and msg.from_.id == bot.config['operator_id']


@bot.msg_task(raw_api_cri)
def raw_api(msg: catbot.Message):
    msg_lines = msg.text.split('\n')
    if msg_lines[0].startswith(f'/api@{bot.username}'):
        action = msg_lines[0].removeprefix(f'/api@{bot.username} ')
    else:
        action = msg_lines[0].removeprefix(f'/api ')

    data = {}
    if len(msg_lines) != 1:
        for line in msg_lines[1:]:
            key = line.split()[0]
            value = line.removeprefix(f'{key} ')
            try:
                value = eval(value)
            except NameError as e:
                bot.send_message(msg.chat.id, text=config['messages']['api_data_error'].format(
                    key=e.args[0].removeprefix("name '").removesuffix("' is not defined")
                ), reply_to_message_id=msg.id)
                return
            else:
                data[key] = value

    try:
        result = bot.api(action=action, data=data)
    except catbot.APIError as e:
        result = e.args[0]
        bot.send_message(msg.chat.id, text=str(result), reply_to_message_id=msg.id)
    else:
        bot.send_message(msg.chat.id, text=str(result), reply_to_message_id=msg.id)
