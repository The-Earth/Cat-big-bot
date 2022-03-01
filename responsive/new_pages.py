import json

import catbot
from responsive import bot, config


def start_new_pages_cri(msg: catbot.Message) -> bool:
    return bot.detect_command('/start_new_pages', msg)


def start_new_pages(msg: catbot.Message):
    new_pages_rec, rec = bot.secure_record_fetch('new_pages', dict)

    if str(msg.chat.id) in new_pages_rec.keys():
        new_pages_rec[str(msg.chat.id)]['enable'] = True
    else:
        new_pages_rec[str(msg.chat.id)] = {'enable': True, 'ns': []}

    rec['new_pages'] = new_pages_rec
    json.dump(rec, open(config['record'], 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
    bot.send_message(msg.chat.id,
                     text=config['messages']['start_new_pages_succ'].format(ns=new_pages_rec[str(msg.chat.id)]["ns"]),
                     reply_to_message_id=msg.id)


def stop_new_pages_cri(msg: catbot.Message) -> bool:
    return bot.detect_command('/stop_new_pages', msg)


def stop_new_pages(msg: catbot.Message):
    new_pages_rec, rec = bot.secure_record_fetch('new_pages', list)

    if str(msg.chat.id) in new_pages_rec.keys():
        new_pages_rec[str(msg.chat.id)]['enable'] = False
    else:
        new_pages_rec[str(msg.chat.id)] = {'enable': False, 'ns': []}

    rec['new_pages'] = new_pages_rec
    json.dump(rec, open(config['record'], 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
    bot.send_message(msg.chat.id, text=config['messages']['stop_new_pages_succ'], reply_to_message_id=msg.id)


def list_ns_cri(msg: catbot.Message) -> bool:
    return bot.detect_command('/list_ns', msg)


def list_ns(msg: catbot.Message):
    bot.send_message(msg.chat.id, text=config['messages']['list_ns'], reply_to_message_id=msg.id)


def set_ns_cri(msg: catbot.Message) -> bool:
    return bot.detect_command('/set_ns', msg)


def set_ns(msg: catbot.Message):
    new_pages_rec, rec = bot.secure_record_fetch('new_pages', list)

    user_input_token = msg.text.split(' ')
    if len(user_input_token) == 1:
        bot.send_message(msg.chat.id, text=config['messages']['set_ns_prompt'], reply_to_message_id=msg.id)
        return
    else:
        ns = []
        for item in user_input_token[1:]:
            try:
                ns.append(int(item))
            except ValueError:
                continue

    if str(msg.chat.id) in new_pages_rec.keys():
        new_pages_rec[str(msg.chat.id)]['ns'] = ns
    else:
        new_pages_rec[str(msg.chat.id)] = {'enable': False, 'ns': ns}

    if len(ns) == 0:
        bot.send_message(msg.chat.id, text=config['messages']['set_ns_failed'], reply_to_message_id=msg.id)
    else:
        resp_text: str = config['messages']['set_ns_succ']
        for item in ns:
            resp_text += str(item) + ', '
        resp_text = resp_text.rstrip(', ')
        rec['new_pages'] = new_pages_rec
        json.dump(rec, open(config['record'], 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
        bot.send_message(msg.chat.id, text=resp_text, reply_to_message_id=msg.id)
