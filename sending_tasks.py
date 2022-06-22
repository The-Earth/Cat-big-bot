import json

from catbot.util import html_refer
from sseclient import SSEClient

import catbot

config = json.load(open('config.json', 'r', encoding='utf-8'))

bot = catbot.Bot(config)


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
        bot.send_message(chat_id,
                         text=f'<a href="https://zh.wikipedia.org/wiki/{html_refer(title)}?redirect=no">'
                              f'{html_refer(title)}</a>'
                              f' - <a href="https://zh.wikipedia.org/wiki/Special:Contributions/{user}"'
                              f'>{user}</a>',
                         parse_mode='HTML')
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


if __name__ == '__main__':
    from requests.exceptions import HTTPError, ConnectionError
    while True:
        try:
            new_pages()
        except (HTTPError, ConnectionError, ConnectionResetError):
            continue
