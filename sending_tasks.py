import json

from sseclient import SSEClient

import catbot

config = json.load(open('config.json', 'r', encoding='utf-8'))

bot = catbot.Bot(config)


def new_pages():
    event_url = 'https://stream.wikimedia.org/v2/stream/page-create'
    ssekw = {'proxies': {'https': config['proxy']['proxy_url']}} if config['proxy']['enable'] else {}
    for event in SSEClient(event_url, **ssekw):
        if event.event == 'message':
            try:
                change = json.loads(event.data)
            except ValueError:
                continue
            else:
                if change['meta']['domain'] != 'zh.wikipedia.org':
                    continue
                title = change['page_title']
                user = change['performer']['user_text']
                if change['page_namespace'] != 0:
                    sending_trials(config['new_pages']['all'], title, user)
                    continue

                sending_trials(config['new_pages']['all'], title, user)
                sending_trials(config['new_pages']['main'], title, user)


def sending_trials(chat_id: int, title: str, user: str):
    for i in range(5):
        try:
            bot.send_message(chat_id,
                             text=f'<a href="https://zh.wikipedia.org/wiki/{title}?redirect=no">{title}</a>'
                                  f' - <a href="https://zh.wikipedia.org/wiki/Special:Contributions/{user}"'
                                  f'>{user}</a>',
                             parse_mode='HTML')
        except catbot.APIError:
            print(f'Retrying {title} ... {i + 1}')
            continue
        else:
            print(title)
            break


if __name__ == '__main__':
    from requests.exceptions import HTTPError
    while True:
        try:
            new_pages()
        except HTTPError:
            continue
