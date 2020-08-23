import json

import catbot
from responsive import bot, config
from responsive import record_empty_test, command_detector
from responsive import trusted


@trusted
def set_trusted_cri(msg: catbot.Message) -> bool:
    return command_detector('/set_trusted', msg)


def set_trusted(msg: catbot.Message):
    trusted_list, rec = record_empty_test('trusted', list)

    new_trusted_id = []
    if msg.reply:
        new_trusted_id.append(msg.reply_to_message.from_.id)
    else:
        user_input_token = msg.text.split()
        if len(user_input_token) == 1:
            bot.send_message(msg.chat.id, text=config['messages']['set_trusted_prompt'], reply_to_message_id=msg.id)
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
        bot.send_message(msg.chat.id, text=config['messages']['set_trusted_failed'], reply_to_message_id=msg.id)
    else:
        reply_text = config['messages']['set_trusted_succ']
        for item in delta:
            reply_text += str(item) + '\n'

        rec['trusted'] = list(trusted_set)
        json.dump(rec, open(config['record'], 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
        bot.send_message(msg.chat.id, text=reply_text, reply_to_message_id=msg.id)


@trusted
def list_trusted_cri(msg: catbot.Message) -> bool:
    return command_detector('/list_trusted', msg) and msg.chat.type != 'private'


def list_trusted(msg: catbot.Message):
    trusted_list, rec = record_empty_test('trusted', list)

    resp_list = []
    bot.send_message(msg.chat.id, text=config['messages']['list_user_pre'], reply_to_message_id=msg.id)
    for trusted_id in trusted_list:
        try:
            trusted_user = bot.get_chat_member(msg.chat.id, trusted_id)
            if trusted_user.status == 'left' or trusted_user.status == 'kicked':
                continue
        except catbot.UserNotFoundError:
            continue
        else:
            resp_list.append(trusted_user)

    resp_text: str = config['messages']['list_trusted_succ']
    for user in resp_list:
        resp_text += f'{user.name}、'
    resp_text = resp_text.rstrip('、')
    if len(resp_list) == 0:
        resp_text = config['messages']['list_trusted_empty']

    bot.send_message(msg.chat.id, text=resp_text, reply_to_message_id=msg.id)
