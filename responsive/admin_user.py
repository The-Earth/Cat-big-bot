import json

import catbot
from responsive import bot, config
from responsive import record_empty_test, command_detector


def set_admin_cri(msg: catbot.Message) -> bool:
    return command_detector('/set_admin', msg) and msg.from_.id == config['operator_id']


def set_admin(msg: catbot.Message):
    admin_list, rec = record_empty_test('admin', list)

    new_admin_id = []
    if msg.reply:
        new_admin_id.append(msg.reply_to_message.from_.id)
    else:
        user_input_token = msg.text.split()
        if len(user_input_token) == 1:
            bot.send_message(msg.chat.id, text=config['messages']['set_admin_prompt'], reply_to_message_id=msg.id)
            return
        else:
            for item in user_input_token[1:]:
                try:
                    new_admin_id.append(int(item))
                except ValueError:
                    continue

    admin_set = set(admin_list)
    old_admin_set = admin_set.copy()
    admin_set.update(new_admin_id)
    delta = admin_set - old_admin_set
    if len(delta) == 0:
        bot.send_message(msg.chat.id, text=config['messages']['set_admin_failed'], reply_to_message_id=msg.id)
    else:
        reply_text = config['messages']['set_admin_succ']
        for item in delta:
            reply_text += str(item) + '\n'

        rec['admin'] = list(admin_set)
        json.dump(rec, open(config['record'], 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
        bot.send_message(msg.chat.id, text=reply_text, reply_to_message_id=msg.id)
