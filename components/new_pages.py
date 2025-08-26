import json

import catbot
import requests
from catbot.util import html_escape
from components import bot
from requests_sse import EventSource, InvalidStatusCodeError, InvalidContentTypeError

__all__ = [
    'start_new_pages',
    'stop_new_pages',
    'list_ns',
    'set_ns',
    'new_pages_main'
]


def start_new_pages_cri(msg: catbot.Message) -> bool:
    return bot.detect_command('/start_new_pages', msg)


@bot.msg_task(start_new_pages_cri)
def start_new_pages(msg: catbot.Message):
    if 'new_pages' in bot.record:
        new_pages_rec = bot.record['new_pages']
    else:
        new_pages_rec = {}

    if str(msg.chat.id) in new_pages_rec.keys():
        new_pages_rec[str(msg.chat.id)]['enable'] = True
    else:
        new_pages_rec[str(msg.chat.id)] = {'enable': True, 'ns': []}

    bot.record['new_pages'] = new_pages_rec
    bot.send_message(
        msg.chat.id,
        text=bot.config['messages']['start_new_pages_succ'].format(ns=new_pages_rec[str(msg.chat.id)]["ns"]),
        reply_to_message_id=msg.id
    )


def stop_new_pages_cri(msg: catbot.Message) -> bool:
    return bot.detect_command('/stop_new_pages', msg)


@bot.msg_task(stop_new_pages_cri)
def stop_new_pages(msg: catbot.Message):
    if 'new_pages' in bot.record:
        new_pages_rec = bot.record['new_pages']
    else:
        new_pages_rec = {}

    if str(msg.chat.id) in new_pages_rec.keys():
        new_pages_rec[str(msg.chat.id)]['enable'] = False
    else:
        new_pages_rec[str(msg.chat.id)] = {'enable': False, 'ns': []}

    bot.record['new_pages'] = new_pages_rec
    bot.send_message(msg.chat.id, text=bot.config['messages']['stop_new_pages_succ'], reply_to_message_id=msg.id)


def list_ns_cri(msg: catbot.Message) -> bool:
    return bot.detect_command('/list_ns', msg)


@bot.msg_task(list_ns_cri)
def list_ns(msg: catbot.Message):
    bot.send_message(msg.chat.id, text=bot.config['messages']['list_ns'], reply_to_message_id=msg.id)


def set_ns_cri(msg: catbot.Message) -> bool:
    return bot.detect_command('/set_ns', msg)


@bot.msg_task(set_ns_cri)
def set_ns(msg: catbot.Message):
    if 'new_pages' in bot.record:
        new_pages_rec = bot.record['new_pages']
    else:
        new_pages_rec = {}

    user_input_token = msg.text.split(' ')
    if len(user_input_token) == 1:
        bot.send_message(msg.chat.id, text=bot.config['messages']['set_ns_prompt'], reply_to_message_id=msg.id)
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
        bot.send_message(msg.chat.id, text=bot.config['messages']['set_ns_failed'], reply_to_message_id=msg.id)
    else:
        resp_text: str = bot.config['messages']['set_ns_succ']
        for item in ns:
            resp_text += str(item) + ', '
        resp_text = resp_text.rstrip(', ')
        bot.record['new_pages'] = new_pages_rec
        bot.send_message(msg.chat.id, text=resp_text, reply_to_message_id=msg.id)


def new_pages(stop_event):
    event_url = 'https://stream.wikimedia.org/v2/stream/page-create'
    sse_kw = {'proxies': {'https': bot.config['proxy']['proxy_url']}} if bot.config['proxy']['enable'] else {}
    sse_kw.update({'headers': {'User-Agent': bot.config['user_agent']}})
    with EventSource(event_url, **sse_kw) as source:
        try:
            for event in source:
                if stop_event.is_set():
                    break
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

                    if 'new_pages' in bot.record:
                        new_pages_rec = bot.record['new_pages']
                    else:
                        new_pages_rec = {}

                    for chat_id in new_pages_rec.keys():
                        if not new_pages_rec[chat_id]['enable']:
                            continue
                        if -1 in new_pages_rec[chat_id]['ns']:
                            sending_trials(int(chat_id), title, user)
                        elif change['page_namespace'] in new_pages_rec[chat_id]['ns']:
                            sending_trials(int(chat_id), title, user)

                    print(title)
        except InvalidStatusCodeError:
            pass
        except InvalidContentTypeError:
            pass
        except requests.RequestException:
            pass
        except StopIteration:
            pass


def sending_trials(chat_id: int, title: str, user: str):
    try:
        text = f'<a href="https://zh.wikipedia.org/wiki/{html_escape(title)}?redirect=no">{html_escape(title)}</a>' \
               f' - <a href="https://zh.wikipedia.org/wiki/Special:Contributions/{user}">{user}</a>'
        bot.send_message(chat_id, text=text, parse_mode='HTML')
    except catbot.APIError as e:
        print(e.args[0])
        if 'user is deactivated' in e.args[0] or 'chat_not found' in e.args[0]:
            print(f'Removing {chat_id}')
            try:
                if 'new_pages' in bot.record:
                    new_pages_rec = bot.record['new_pages']
                else:
                    new_pages_rec = {}
                new_pages_rec.pop(str(chat_id), '')
                bot.record = new_pages_rec
            except KeyError:
                pass


def new_pages_main(stop_event):
    from requests.exceptions import HTTPError, ConnectionError
    while not stop_event.is_set():
        try:
            new_pages(stop_event)
        except (HTTPError, ConnectionError, ConnectionResetError):
            continue
        except KeyboardInterrupt:
            break
