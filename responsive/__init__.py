import json
import multiprocessing
import threading

import catbot

config = json.load(open('config.json', 'r', encoding='utf-8'))
bot = catbot.Bot(config)
t_lock = threading.Lock()
p_lock = multiprocessing.Lock()


def command_detector(cmd: str, msg: catbot.Message) -> bool:
    if cmd in msg.commands:
        return msg.text.startswith(cmd)
    elif f'{cmd}@{bot.username}' in msg.commands:
        return msg.text.startswith(f'{cmd}@{bot.username}')
    else:
        return False


def record_empty_test(key: str, data_type, file=config['record']):
    """
    :param key: Name of the data you want in record file
    :param data_type: Type of the data. For example, if it is trusted user list, data_type will be list.
    :param file: Control the file to read as record
    :return: Returns a tuple. The first element is the data you asked for. The second is the deserialized record file.
    """
    try:
        rec = json.load(open(file, 'r', encoding='utf-8'))
    except FileNotFoundError:
        record_list, rec = data_type(), {}
        json.dump({key: record_list}, open(file, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
    else:
        if key in rec.keys():
            record_list = rec[key]
        else:
            record_list = data_type()

    return record_list, rec


def trusted(func):
    """
    Decorate criteria functions. Decorated functions return False if the user who sent the message is not listed in
    trusted user list, which is defined in config['trusted_rec']. That means, only trusted users are allowed to perform
    decorated operations. Requests from other users are ignored. As defined in catbot.Bot.add_msg_task() and
    catbot.Bot.add_query_task, the first positional argument of the decorated function should be a catbot.Message()
    object, which is created from the update stream.
    """

    def wrapper(*args, **kwargs):
        trusted_list = record_empty_test('trusted', list)[0]
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
        blocked_list = record_empty_test('blocked', list)[0]
        msg = args[0]
        if msg.from_.id in blocked_list:
            return False

        return func(*args, **kwargs)

    return wrapper


def voter(func):
    """
    Similar to trusted, limit vote right to voters.
    """

    def wrapper(*args, **kwargs):
        voter_list = record_empty_test('voter', list)[0]
        msg = args[0]
        if msg.from_.id in voter_list:
            return func(*args, **kwargs)
        else:
            return False

    return wrapper
