import json

import catbot
from catbot.util import html_refer
from components import bot, config
from sseclient import SSEClient


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


def new_pages():
    event_url = 'https://stream.wikimedia.org/v2/stream/page-create'
    ssekw = {'proxies': {'https': config['proxy']['proxy_url']}} if config['proxy']['enable'] else {}
    for event in SSEClient(event_url, **ssekw):
        if event.event != 'message':
            continue
        try:
            change: dict = json.loads(event.data)
        except ValueError:
            continue
        else:
            if change['meta']['domain'] != 'zh.wikipedia.org':
                continue
            title: str = change['page_title']
            user: str = change['performer']['user_text']

            try:
                new_pages_rec = json.load(open(config['record'], 'r', encoding='utf-8'))['new_pages']
            except FileNotFoundError:
                json.dump({'new_pages': {}}, open(config['record'], 'w', encoding='utf-8'), indent=2,
                          ensure_ascii=False)
                continue
            except KeyError:
                rec = json.load(open(config['record'], 'r', encoding='utf-8'))
                rec['new_pages'] = {}
                json.dump(rec, open(config['record'], 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
                continue

            for chat_id in new_pages_rec.keys():
                if not new_pages_rec[chat_id]['enable']:
                    continue
                if -1 in new_pages_rec[chat_id]['ns']:
                    sending_trials(int(chat_id), title, user)
                elif change['page_namespace'] in new_pages_rec[chat_id]['ns']:
                    sending_trials(int(chat_id), title, user)

            print(title)


def sending_trials(chat_id: int, title: str, user: str):
    try:
        text = f'<a href="https://zh.wikipedia.org/wiki/{html_refer(title)}?redirect=no">{html_refer(title)}</a>' \
               f' - <a href="https://zh.wikipedia.org/wiki/Special:Contributions/{user}">{user}</a>',
        bot.send_message(chat_id, text, parse_mode='HTML')
    except catbot.APIError as e:
        print(e.args[0])
        if 'user is deactivated' in e.args[0]:
            print(f'{chat_id} is deactivated, removing it from settings.')
            try:
                rec: dict = json.load(open(config['record'], 'r', encoding='utf-8'))
                new_pages_rec: dict = rec['new_pages']
                new_pages_rec.pop(str(chat_id))
                json.dump(rec, open(config['record'], 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
            except KeyError:
                pass


def new_pages_main():
    from requests.exceptions import HTTPError, ConnectionError
    while True:
        try:
            new_pages()
        except (HTTPError, ConnectionError, ConnectionResetError):
            continue
