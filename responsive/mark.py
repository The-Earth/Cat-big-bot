import json

import catbot
from responsive import bot, config
from responsive import record_empty_test, command_detector
from responsive import trusted


def mark_cri(msg: catbot.Message) -> bool:
    return command_detector('/mark', msg)


def mark(msg: catbot.Message):
    mark_rec, rec = record_empty_test('mark', dict)

    if msg.chat.link == '':
        bot.send_message(msg.chat.id, text=config['messages']['mark_private'], reply_to_message_id=msg.id)
        return
    if not msg.reply:
        bot.send_message(msg.chat.id, text=config['messages']['mark_empty_reply'], reply_to_message_id=msg.id)
        return
    reply_to_id = msg.reply_to_message.id

    comment = msg.html_formatted_text.lstrip('/mark')

    if str(msg.chat.id) not in mark_rec.keys():
        mark_rec[str(msg.chat.id)] = [{'id': reply_to_id, 'comment': comment}]
    else:
        mark_rec[str(msg.chat.id)].append({'id': reply_to_id, 'comment': comment})
    rec['mark'] = mark_rec
    json.dump(rec, open(config['record'], 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
    bot.send_message(msg.chat.id, text=config['messages']['mark_succ'], reply_to_message_id=msg.id)


def list_marked_cri(msg: catbot.Message) -> bool:
    return command_detector('/list_marked', msg)


def list_marked(msg: catbot.Message):
    mark_rec, rec = record_empty_test('mark', dict)

    if msg.chat.link == '':
        bot.send_message(msg.chat.id, text=config['messages']['mark_private'], reply_to_message_id=msg.id)
        return

    if str(msg.chat.id) not in mark_rec.keys() or len(mark_rec[str(msg.chat.id)]) == 0:
        bot.send_message(msg.chat.id, text=config['messages']['mark_list_empty'], reply_to_message_id=msg.id)
    else:
        text = ''
        for record in mark_rec[str(msg.chat.id)]:
            text += f'{msg.chat.link}/{record["id"]} {record["comment"]}\n'
        bot.send_message(msg.chat.id, text=text, reply_to_message_id=msg.id, disable_web_page_preview=True,
                         parse_mode='HTML')


@trusted
def unmark_cri(msg: catbot.Message) -> bool:
    return command_detector('/unmark', msg)


def unmark(msg: catbot.Message):
    mark_rec, rec = record_empty_test('mark', dict)

    if msg.chat.link == '':
        bot.send_message(msg.chat.id, text=config['messages']['mark_private'], reply_to_message_id=msg.id)
        return
    if str(msg.chat.id) not in mark_rec.keys() or len(mark_rec[str(msg.chat.id)]) == 0:
        bot.send_message(msg.chat.id, text=config['messages']['mark_list_empty'], reply_to_message_id=msg.id)
        return

    unmark_list = []
    if msg.reply:
        unmark_list.append(msg.reply_to_message.id)
    else:
        user_input_token = msg.text.split()
        if len(user_input_token) == 1:
            bot.send_message(msg.chat.id, text=config['messages']['mark_unmark_prompt'], reply_to_message_id=msg.id)
            return
        else:
            for item in user_input_token[1:]:
                try:
                    unmark_list.append(int(item))
                except ValueError:
                    continue

    response_text = config['messages']['mark_unmark_succ']
    i = 0
    while i < len(mark_rec[str(msg.chat.id)]):
        if mark_rec[str(msg.chat.id)][i]['id'] in unmark_list:
            unmarked_id = mark_rec[str(msg.chat.id)][i]['id']
            mark_rec[str(msg.chat.id)].pop(i)
            rec['mark'] = mark_rec
            json.dump(rec, open(config['record'], 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
            response_text += str(unmarked_id) + '\n'
        else:
            i += 1

    if response_text != config['messages']['mark_unmark_succ']:
        bot.send_message(msg.chat.id, text=response_text, reply_to_message_id=msg.id)
    else:
        bot.send_message(msg.chat.id, text=config['messages']['mark_unmark_failed'], reply_to_message_id=msg.id)
