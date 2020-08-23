import json

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
            if 'comment' in change.keys():
                comment: str = change['comment']
            else:
                comment = ''

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
                    sending_trials(int(chat_id), title, user, comment)
                elif change['page_namespace'] in new_pages_rec[chat_id]['ns']:
                    sending_trials(int(chat_id), title, user, comment)

            print(title)


def sending_trials(chat_id: int, title: str, user: str, comment: str):
    for i in range(5):
        try:
            bot.send_message(chat_id,
                             text=f'[{title}](https://zh.wikipedia.org/wiki/{title}?redirect=no)'
                                  f' - [{user}](https://zh.wikipedia.org/wiki/Special:Contributions/{user})'
                                  f' ({comment})',
                             parse_mode='MarkdownV2')
        except catbot.APIError as e:
            print(e.args[0])
            print(f'Retrying {title} ... {i + 1}')
            continue
        else:
            break


if __name__ == '__main__':
    from requests.exceptions import HTTPError
    while True:
        try:
            new_pages()
        except HTTPError:
            continue
