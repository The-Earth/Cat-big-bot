import json
import time
from threading import Thread

from sseclient import SSEClient
from telegram.ext import Updater, CommandHandler

config = json.load(open('config.json', 'r', encoding='utf-8'))
if config['proxy']['enable']:
    updater = Updater(token=config['token'], use_context=True,
                      request_kwargs={'proxy_url': config['proxy']['proxy_url']})
else:
    updater = Updater(token=config['token'], use_context=True)
dispatcher = updater.dispatcher


def group_id(update, context):
    chat_id = update.effective_chat.id
    context.bot.send_message(chat_id=chat_id, text=chat_id)


group_id_handler = CommandHandler('group_id', group_id)
dispatcher.add_handler(group_id_handler)

t1 = Thread(target=updater.start_polling, daemon=True)


def new_pages_main(chat_id):
    event_url = 'https://stream.wikimedia.org/v2/stream/page-create'
    ssekw = {'proxies': {'https': config['proxy']['proxy_url']}} if config['proxy']['enable'] else {}
    for event in SSEClient(event_url, **ssekw):
        if event.event == 'message':
            try:
                change = json.loads(event.data)
            except ValueError:
                pass
            else:
                if change['meta']['domain'] != 'zh.wikipedia.org':
                    continue
                if change['page_namespace'] != 0:
                    continue
                title = change['page_title']
                user = change['performer']['user_text']
                updater.bot.send_message(chat_id,
                                         f'<a href="https://zh.wikipedia.org/wiki/{title}?redirect=no">{title}</a>'
                                         f' - <a href="https://zh.wikipedia.org/wiki/Special:Contributions/{user}">{user}</a>',
                                         parse_mode='HTML')
                print(title)


def new_pages(chat_id):
    try:
        new_pages_main(chat_id)
    except Exception:
        updater.bot.send_message(chat_id, config['message_bot_stopped'])
        raise


t2 = Thread(target=new_pages, args=(config['new_pages']['chat_id'],), daemon=True)

t1.start()
t2.start()

while True:
    time.sleep(60)
