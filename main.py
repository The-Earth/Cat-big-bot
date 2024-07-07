from multiprocessing import Event
from threading import Thread

from components import bot
from components.new_pages import new_pages_main
from components.poll import stop_poll_scheduled_main
from components.spam_detection import porn_detect_main


def bot_run(stop_event: Event):
    with bot:
        bot.start(stop_event, timeout=5, print_log=True)
    return


if __name__ == '__main__':
    event = Event()
    scheduled_stop_poll_p = Thread(target=stop_poll_scheduled_main, args=(event,))
    scheduled_stop_poll_p.start()
    bot_p = Thread(target=bot_run, args=(event,))
    bot_p.start()
    new_pages_p = Thread(target=new_pages_main, args=(event,))
    new_pages_p.start()
    porn_detect_p = Thread(target=porn_detect_main, daemon=True)
    porn_detect_p.start()

    import time
    while True:
        try:
            time.sleep(3600)
        except KeyboardInterrupt:
            event.set()
            break
