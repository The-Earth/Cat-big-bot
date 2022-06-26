import json
import multiprocessing
import threading

import catbot

config = json.load(open('config.json', 'r', encoding='utf-8'))
bot = catbot.Bot(config)
t_lock = threading.Lock()
p_lock = multiprocessing.Lock()


def trusted(func):
    """
    Decorate criteria functions. Decorated functions return False if the user who sent the message is not listed in
    trusted user list, which is defined in config['trusted_rec']. That means, only trusted users are allowed to perform
    decorated operations. Requests from other users are ignored. As defined in catbot.Bot.add_msg_task() and
    catbot.Bot.add_query_task, the first positional argument of the decorated function should be a catbot.Message()
    object, which is created from the update stream.
    """

    def wrapper(*args, **kwargs):
        trusted_list = bot.secure_record_fetch('trusted', list)[0]
        msg = args[0]  # might be Message or CallbackQuery, both of which have the "from_" attr
        if msg.from_.id in trusted_list:
            return func(*args, **kwargs)
        elif msg.from_.id == config['operator_id']:
            return func(*args, **kwargs)
        else:
            return False

    return wrapper


def blocked(func):
    """
    Similar to trusted(), block messages from those who are in the "blocked" list.
    """

    def wrapper(*args, **kwargs):
        blocked_list = bot.secure_record_fetch('blocked', list)[0]
        msg = args[0]
        if msg.from_.id in blocked_list:
            return False

        return func(*args, **kwargs)

    return wrapper
