from __future__ import annotations

import catbot

from components import t_lock, bot

__all__ = [
    'trusted',
    'blocked'
]


def trusted(func):
    """
    Decorate criteria functions. Decorated functions return False if the user who sent the message is not listed in
    trusted user list, which is defined in bot.config['trusted']. That means, only trusted users are allowed to perform
    decorated operations. Requests from other users are ignored. As defined in catbot.Bot.add_msg_task() and
    catbot.Bot.add_query_task, the first positional argument of the decorated function should be a catbot.Message()
    object, which is created from the update stream.
    """
    def wrapper(*args, **kwargs):
        with t_lock:
            if 'trusted' in bot.record:
                trusted_list: list[int] = bot.record['trusted']
            else:
                trusted_list = []
        msg: catbot.Message | catbot.CallbackQuery = args[0]
        if msg.from_.id in trusted_list:
            return func(*args, **kwargs)
        elif msg.from_.id == bot.config['operator_id']:
            return func(*args, **kwargs)
        else:
            return False

    return wrapper


def blocked(func):
    """
    Similar to trusted(), block messages from those who are in the "blocked" list.
    """
    def wrapper(*args, **kwargs):
        with t_lock:
            if 'blocked' in bot.record:
                blocked_list: list[int] = bot.record['blocked']
            else:
                blocked_list = []
        msg: catbot.Message = args[0]
        if msg.from_.id in blocked_list:
            return False

        return func(*args, **kwargs)

    return wrapper
