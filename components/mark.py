import catbot
from components import bot
from components.decorators import trusted

__all__ = [
    'mark',
    'list_marked',
    'unmark'
]


def mark_cri(msg: catbot.Message) -> bool:
    return bot.detect_command('/mark', msg)


@bot.msg_task(mark_cri)
def mark(msg: catbot.Message):
    if not str(msg.chat.id).startswith('-100'):
        bot.send_message(msg.chat.id, text=bot.config['messages']['mark_private'], reply_to_message_id=msg.id)
        return
    if not msg.reply:
        bot.send_message(msg.chat.id, text=bot.config['messages']['mark_empty_reply'], reply_to_message_id=msg.id)
        return
    reply_to_id = msg.reply_to_message.id

    if msg.html_formatted_text.startswith(f'/mark@{bot.username}'):
        comment = msg.html_formatted_text.removeprefix(f'/mark@{bot.username}').lstrip()
    else:
        comment = msg.html_formatted_text.removeprefix('/mark').lstrip()

    if 'mark' in bot.record:
        mark_rec = bot.record['mark']
    else:
        mark_rec = {}

    if str(msg.chat.id) not in mark_rec.keys():
        mark_rec[str(msg.chat.id)] = [{'id': reply_to_id, 'comment': comment}]
    else:
        mark_rec[str(msg.chat.id)].append({'id': reply_to_id, 'comment': comment})

    if len(mark_rec[str(msg.chat.id)]) > 100:
        mark_rec[str(msg.chat.id)] = mark_rec[str(msg.chat.id)][-100:]
    bot.record['mark'] = mark_rec
    bot.send_message(msg.chat.id, text=bot.config['messages']['mark_succ'], reply_to_message_id=msg.id)


def list_marked_cri(msg: catbot.Message) -> bool:
    return bot.detect_command('/list_marked', msg)


@bot.msg_task(list_marked_cri)
def list_marked(msg: catbot.Message):
    if not str(msg.chat.id).startswith('-100'):
        bot.send_message(msg.chat.id, text=bot.config['messages']['mark_private'], reply_to_message_id=msg.id)
        return

    if 'mark' in bot.record:
        mark_rec = bot.record['mark']
    else:
        mark_rec = {}
    if str(msg.chat.id) not in mark_rec.keys() or len(mark_rec[str(msg.chat.id)]) == 0:
        bot.send_message(msg.chat.id, text=bot.config['messages']['mark_list_empty'], reply_to_message_id=msg.id)
    else:
        text = ''
        for record in mark_rec[str(msg.chat.id)]:
            text += (f'<a href="https://t.me/c/{str(msg.chat.id).replace("-100", "")}/'
                     f'{record["id"]}">{record["id"]}</a> {record["comment"]}\n')
        bot.send_message(msg.chat.id, text=text, reply_to_message_id=msg.id, disable_web_page_preview=True,
                         parse_mode='HTML')


@trusted
def unmark_cri(msg: catbot.Message) -> bool:
    return bot.detect_command('/unmark', msg)


@bot.msg_task(unmark_cri)
def unmark(msg: catbot.Message):
    if 'mark' in bot.record:
        mark_rec = bot.record['mark']
    else:
        mark_rec = {}

    if not str(msg.chat.id).startswith('-100'):
        bot.send_message(msg.chat.id, text=bot.config['messages']['mark_private'], reply_to_message_id=msg.id)
        return
    if str(msg.chat.id) not in mark_rec.keys() or len(mark_rec[str(msg.chat.id)]) == 0:
        bot.send_message(msg.chat.id, text=bot.config['messages']['mark_list_empty'], reply_to_message_id=msg.id)
        return

    unmark_list = []
    if msg.reply:
        unmark_list.append(msg.reply_to_message.id)
    else:
        user_input_token = msg.text.split()
        if len(user_input_token) == 1:
            bot.send_message(msg.chat.id, text=bot.config['messages']['mark_unmark_prompt'], reply_to_message_id=msg.id)
            return
        else:
            for item in user_input_token[1:]:
                try:
                    unmark_list.append(int(item))
                except ValueError:
                    continue

    response_text = bot.config['messages']['mark_unmark_succ']
    i = 0

    while i < len(mark_rec[str(msg.chat.id)]):
        if mark_rec[str(msg.chat.id)][i]['id'] in unmark_list:
            unmarked_id = mark_rec[str(msg.chat.id)][i]['id']
            mark_rec[str(msg.chat.id)].pop(i)
            response_text += str(unmarked_id) + '\n'
        else:
            i += 1
    bot.record['mark'] = mark_rec

    if response_text != bot.config['messages']['mark_unmark_succ']:
        bot.send_message(msg.chat.id, text=response_text, reply_to_message_id=msg.id)
    else:
        bot.send_message(msg.chat.id, text=bot.config['messages']['mark_unmark_failed'], reply_to_message_id=msg.id)
