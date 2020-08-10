import json

import catbot

config = json.load(open('config.json', 'r', encoding='utf-8'))

bot = catbot.Bot(config)


def command_detector(cmd: str, msg: catbot.Message) -> bool:
    if cmd in msg.commands:
        return msg.text.startswith(cmd)
    elif f'{cmd}@{bot.username}' in msg.commands:
        return msg.text.startswith(f'{cmd}@{bot.username}')
    else:
        return False


def record_empty_test(key: str, data_type):
    try:
        rec = json.load(open(config['record'], 'r', encoding='utf-8'))
    except FileNotFoundError:
        record_list, rec = data_type(), {}
        json.dump({key: record_list}, open(config['record'], 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
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
    decorated operations. Requests from other users are ignored. As defined in catbot.Bot.add_task(), the first
    positional argument of the decorated function should be a catbot.Message() object, which is created from the update
    stream.
    """

    def wrapper(*args, **kwargs):
        trusted_list = record_empty_test('trusted', list)[0]
        msg: catbot.Message = args[0]
        if msg.from_.id not in trusted_list and msg.from_.id != config['operator_id']:
            return False

        return func(*args, **kwargs)

    return wrapper


def blocked(func):
    """
    Similar to trusted(), block messages from those who are in the "blocked" list.
    """

    def wrapper(*args, **kwargs):
        blocked_list = record_empty_test('blocked', list)[0]
        msg: catbot.Message = args[0]
        if msg.from_.id in blocked_list:
            return False

        return func(*args, **kwargs)

    return wrapper


def get_user_id_cri(msg: catbot.Message) -> bool:
    return command_detector('/user_id', msg)


def get_user_id(msg: catbot.Message):
    if msg.reply:
        res_id = msg.reply_to_message.from_.id
    else:
        res_id = msg.from_.id
    bot.send_message(chat_id=msg.chat.id, text=res_id, reply_to_message_id=msg.id)


def get_chat_id_cri(msg: catbot.Message) -> bool:
    return command_detector('/chat_id', msg)


def get_chat_id(msg: catbot.Message):
    bot.send_message(chat_id=msg.chat.id, text=msg.chat.id, reply_to_message_id=msg.id)


@blocked
def pass_on_cri(msg: catbot.Message) -> bool:
    return command_detector('/pass', msg) and msg.chat.type == 'private'


def pass_on(msg: catbot.Message):
    from_username = '@' + msg.from_.username if msg.from_.username != '' else 'No username'
    text = msg.text.lstrip('/pass ')
    try:
        bot.send_message(chat_id=config['operator_id'],
                         text=config['messages']['pass_on_new_msg_to_op'].format(from_id=msg.from_.id,
                                                                                 from_name=msg.from_.name,
                                                                                 from_username=from_username,
                                                                                 text=text),
                         parse_mode='HTML')
    except catbot.APIError:
        bot.send_message(chat_id=msg.from_.id, text=config['messages']['pass_on_sending_failed'])
        raise
    else:
        bot.send_message(chat_id=msg.from_.id, text=config['messages']['pass_on_sent_to_op_succ'])


def reply_cri(msg: catbot.Message) -> bool:
    return command_detector('/reply', msg) and msg.chat.id == config['operator_id']


def reply(msg: catbot.Message):
    text = msg.text.lstrip('/reply ')
    to_id = text.split(' ')[0]
    content = ' '.join(text.split(' ')[1:])
    try:
        bot.send_message(chat_id=to_id, text=config['messages']['pass_on_reply_from_op'].format(content=content))
    except catbot.APIError as ex:
        if 'chat not found' in ex.args[0]:
            bot.send_message(chat_id=config['operator_id'],
                             text=config['messages']['pass_on_reply_invalid_id'])
        else:
            bot.send_message(chat_id=config['operator_id'], text=config['messages']['pass_on_sending_failed'])
            raise
    else:
        bot.send_message(chat_id=config['operator_id'],
                         text=config['messages']['pass_on_reply_succ'].format(to_id=to_id))


def start_cri(msg: catbot.Message) -> bool:
    return command_detector('/start', msg) and msg.chat.type == 'private'


def start(msg: catbot.Message):
    bot.send_message(chat_id=msg.chat.id, text=config['messages']['start'])


def mark_cri(msg: catbot.Message) -> bool:
    return command_detector('/mark', msg)


def mark(msg: catbot.Message):
    mark_rec, rec = record_empty_test('mark', dict)

    if msg.chat.link == '':
        bot.send_message(msg.chat.id, text=config['messages']['mark_private'], reply_to_message_id=msg.id)
        return
    if not msg.reply:
        bot.send_message(msg.chat.id, text=config['messages']['mark_empty_reply'], reply_to_message_id=msg.id)
        return
    reply_to_id = msg.reply_to_message.id

    comment = msg.text.lstrip('/mark')

    if str(msg.chat.id) not in mark_rec.keys():
        mark_rec[str(msg.chat.id)] = [{'id': reply_to_id, 'comment': comment}]
    else:
        mark_rec[str(msg.chat.id)].append({'id': reply_to_id, 'comment': comment})
    rec['mark'] = mark_rec
    json.dump(rec, open(config['record'], 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
    bot.send_message(msg.chat.id, text=config['messages']['mark_succ'], reply_to_message_id=msg.id)


def list_marked_cri(msg: catbot.Message) -> bool:
    return command_detector('/list_marked', msg)


def list_marked(msg: catbot.Message):
    mark_rec, rec = record_empty_test('mark', dict)

    if msg.chat.link == '':
        bot.send_message(msg.chat.id, text=config['messages']['mark_private'], reply_to_message_id=msg.id)
        return

    if str(msg.chat.id) not in mark_rec.keys() or len(mark_rec[str(msg.chat.id)]) == 0:
        bot.send_message(msg.chat.id, text=config['messages']['mark_list_empty'], reply_to_message_id=msg.id)
    else:
        text = ''
        for record in mark_rec[str(msg.chat.id)]:
            text += f'{msg.chat.link}/{record["id"]} {record["comment"]}\n'
        bot.send_message(msg.chat.id, text=text, reply_to_message_id=msg.id, disable_web_page_preview=True)


@trusted
def unmark_cri(msg: catbot.Message) -> bool:
    return command_detector('/unmark', msg)


def unmark(msg: catbot.Message):
    mark_rec, rec = record_empty_test('mark', dict)

    if msg.chat.link == '':
        bot.send_message(msg.chat.id, text=config['messages']['mark_private'], reply_to_message_id=msg.id)
        return
    if str(msg.chat.id) not in mark_rec.keys() or len(mark_rec[str(msg.chat.id)]) == 0:
        bot.send_message(msg.chat.id, text=config['messages']['mark_list_empty'], reply_to_message_id=msg.id)
        return

    unmark_list = []
    if msg.reply:
        unmark_list.append(msg.reply_to_message.id)
    else:
        user_input_token = msg.text.split()
        if len(user_input_token) == 1:
            bot.send_message(msg.chat.id, text=config['messages']['mark_unmark_prompt'], reply_to_message_id=msg.id)
            return
        else:
            for item in user_input_token[1:]:
                try:
                    unmark_list.append(int(item))
                except ValueError:
                    continue

    response_text = config['messages']['mark_unmark_succ']
    i = 0
    while i < len(mark_rec[str(msg.chat.id)]):
        if mark_rec[str(msg.chat.id)][i]['id'] in unmark_list:
            unmarked_id = mark_rec[str(msg.chat.id)][i]['id']
            mark_rec[str(msg.chat.id)].pop(i)
            rec['mark'] = mark_rec
            json.dump(rec, open(config['record'], 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
            response_text += str(unmarked_id) + '\n'
        else:
            i += 1

    if response_text != config['messages']['mark_unmark_succ']:
        bot.send_message(msg.chat.id, text=response_text, reply_to_message_id=msg.id)
    else:
        bot.send_message(msg.chat.id, text=config['messages']['mark_unmark_failed'], reply_to_message_id=msg.id)


@trusted
def set_trusted_cri(msg: catbot.Message) -> bool:
    return command_detector('/set_trusted', msg)


def set_trusted(msg: catbot.Message):
    trusted_list, rec = record_empty_test('trusted', list)

    new_trusted_id = []
    if msg.reply:
        new_trusted_id.append(msg.reply_to_message.from_.id)
    else:
        user_input_token = msg.text.split()
        if len(user_input_token) == 1:
            bot.send_message(msg.chat.id, text=config['messages']['set_trusted_prompt'], reply_to_message_id=msg.id)
            return
        else:
            for item in user_input_token[1:]:
                try:
                    new_trusted_id.append(int(item))
                except ValueError:
                    continue

    trusted_set = set(trusted_list)
    old_trusted_set = trusted_set.copy()
    trusted_set.update(new_trusted_id)
    delta = trusted_set - old_trusted_set
    if len(delta) == 0:
        bot.send_message(msg.chat.id, text=config['messages']['set_trusted_failed'], reply_to_message_id=msg.id)
    else:
        reply_text = config['messages']['set_trusted_succ']
        for item in delta:
            reply_text += str(item) + '\n'

        rec['trusted'] = list(trusted_set)
        json.dump(rec, open(config['record'], 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
        bot.send_message(msg.chat.id, text=reply_text, reply_to_message_id=msg.id)


@trusted
def list_trusted_cri(msg: catbot.Message) -> bool:
    return command_detector('/list_trusted', msg) and msg.chat.type != 'private'


def list_trusted(msg: catbot.Message):
    trusted_list, rec = record_empty_test('trusted', list)

    resp_list = []
    bot.send_message(msg.chat.id, text=config['messages']['list_trusted_pre'], reply_to_message_id=msg.id)
    for trusted_id in trusted_list:
        try:
            trusted_user = bot.get_chat_member(msg.chat.id, trusted_id)
            if trusted_user.status == 'left' or trusted_user.status == 'kicked':
                continue
        except catbot.UserNotFoundError:
            continue
        else:
            resp_list.append(trusted_user)

    resp_text: str = config['messages']['list_trusted_succ']
    for user in resp_list:
        resp_text += f'{user.name}、'
    resp_text = resp_text.rstrip('、')
    if len(resp_list) == 0:
        resp_text = config['messages']['list_trusted_empty']

    bot.send_message(msg.chat.id, text=resp_text, parse_mode='HTML', reply_to_message_id=msg.id)


def bot_help_cri(msg: catbot.Message) -> bool:
    if msg.chat.type == 'private':
        return command_detector('/help', msg)
    else:
        trusted_list = record_empty_test('trusted', list)[0]
        if msg.from_.id not in trusted_list and msg.from_.id != config['operator_id']:
            return False

        return f'/help@{bot.username}' in msg.commands and msg.text.startswith(f'/help@{bot.username}')


def bot_help(msg: catbot.Message):
    if msg.chat.type == 'private':
        resp_text = '\n'.join(config['help']['private'])
        bot.send_message(msg.chat.id, text=resp_text, reply_to_message_id=msg.id)
    else:
        resp_text = '\n'.join(config['help']['public'])
        bot.send_message(msg.chat.id, text=resp_text, reply_to_message_id=msg.id)


def get_permalink_cri(msg: catbot.Message) -> bool:
    return command_detector('/permalink', msg) and msg.chat.type == 'private'


def get_permalink(msg: catbot.Message):
    id_list = []
    user_input_token = msg.text.split()
    if len(user_input_token) == 1:
        bot.send_message(msg.chat.id, text=config['messages']['permalink_prompt'], reply_to_message_id=msg.id)
        return
    else:
        for item in user_input_token[1:]:
            try:
                id_list.append(int(item))
            except ValueError:
                continue

    resp_text = ''
    for item in id_list:
        resp_text += f'<a href="tg://user?id={item}">{item}</a>\n'
    bot.send_message(msg.chat.id, text=resp_text, parse_mode='HTML', reply_to_message_id=msg.id)


def start_new_pages_cri(msg: catbot.Message) -> bool:
    return command_detector('/start_new_pages', msg)


def start_new_pages(msg: catbot.Message):
    new_pages_rec, rec = record_empty_test('new_pages', list)

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
    return command_detector('/stop_new_pages', msg)


def stop_new_pages(msg: catbot.Message):
    new_pages_rec, rec = record_empty_test('new_pages', list)

    if str(msg.chat.id) in new_pages_rec.keys():
        new_pages_rec[str(msg.chat.id)]['enable'] = False
    else:
        new_pages_rec[str(msg.chat.id)] = {'enable': False, 'ns': []}

    rec['new_pages'] = new_pages_rec
    json.dump(rec, open(config['record'], 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
    bot.send_message(msg.chat.id, text=config['messages']['stop_new_pages_succ'], reply_to_message_id=msg.id)


def list_ns_cri(msg: catbot.Message) -> bool:
    return command_detector('/list_ns', msg)


def list_ns(msg: catbot.Message):
    bot.send_message(msg.chat.id, text=config['messages']['list_ns'], reply_to_message_id=msg.id)


def set_ns_cri(msg: catbot.Message) -> bool:
    return command_detector('/set_ns', msg)


def set_ns(msg: catbot.Message):
    new_pages_rec, rec = record_empty_test('new_pages', list)

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


def block_private_cri(msg: catbot.Message) -> bool:
    return command_detector('/block', msg) and msg.chat.id == config['operator_id']


def block_private(msg: catbot.Message):
    blocked_list, rec = record_empty_test('blocked', list)

    user_input_token = msg.text.split()
    id_to_block = []
    if len(user_input_token) == 1:
        bot.send_message(config['operator_id'], text=config['messages']['block_prompt'], reply_to_message_id=msg.id)
        return
    else:
        for item in user_input_token[1:]:
            try:
                id_to_block.append(int(item))
            except ValueError:
                continue

    blocked_set = set(blocked_list)
    old_blocked_set = blocked_set.copy()
    blocked_set.update(id_to_block)
    delta = blocked_set - old_blocked_set
    if len(delta) == 0:
        bot.send_message(config['operator_id'], text=config['messages']['block_failed'], reply_to_message_id=msg.id)
    else:
        reply_text = config['messages']['block_succ']
        for item in delta:
            reply_text += str(item) + '\n'

        rec['blocked'] = list(blocked_set)
        json.dump(rec, open(config['record'], 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
        bot.send_message(config['operator_id'], text=reply_text, reply_to_message_id=msg.id)


def list_block_private_cri(msg: catbot.Message) -> bool:
    return command_detector('/list_blocked', msg) and msg.chat.id == config['operator_id']


def list_block_private(msg: catbot.Message):
    blocked_list = record_empty_test('blocked', list)[0]
    resp_text = ''
    if len(blocked_list) == 0:
        bot.send_message(config['operator_id'], text=config['messages']['list_block_empty'], reply_to_message_id=msg.id)
        return
    for item in blocked_list:
        resp_text += f'<a href="tg://user?id={item}">{item}</a>\n'

    bot.send_message(config['operator_id'], text=resp_text, parse_mode='HTML', reply_to_message_id=msg.id)


def unblock_private_cri(msg: catbot.Message) -> bool:
    return command_detector('/unblock', msg) and msg.chat.id == config['operator_id']


def unblock_private(msg: catbot.Message):
    blocked_list, rec = record_empty_test('blocked', list)

    user_input_token = msg.text.split()
    unblocked_id = []
    if len(user_input_token) == 1:
        bot.send_message(config['operator_id'], text=config['messages']['unblock_prompt'], reply_to_message_id=msg.id)
        return
    else:
        for item in user_input_token[1:]:
            try:
                blocked_list.remove(int(item))
            except ValueError:
                continue
            else:
                unblocked_id.append(item)

    if len(unblocked_id) == 0:
        bot.send_message(config['operator_id'], text=config['messages']['unblock_failed'], reply_to_message_id=msg.id)
    else:
        rec['blocked'] = blocked_list
        json.dump(rec, open(config['record'], 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
        resp_text = config['messages']['unblock_succ'] + '\n'.join(unblocked_id)
        bot.send_message(config['operator_id'], text=resp_text, reply_to_message_id=msg.id)


if __name__ == '__main__':
    bot.add_task(get_user_id_cri, get_user_id)
    bot.add_task(get_chat_id_cri, get_chat_id)
    bot.add_task(pass_on_cri, pass_on)
    bot.add_task(reply_cri, reply)
    bot.add_task(start_cri, start)
    bot.add_task(mark_cri, mark)
    bot.add_task(list_marked_cri, list_marked)
    bot.add_task(unmark_cri, unmark)
    bot.add_task(set_trusted_cri, set_trusted)
    bot.add_task(list_trusted_cri, list_trusted)
    bot.add_task(bot_help_cri, bot_help)
    bot.add_task(get_permalink_cri, get_permalink)
    bot.add_task(list_ns_cri, list_ns)
    bot.add_task(start_new_pages_cri, start_new_pages)
    bot.add_task(stop_new_pages_cri, stop_new_pages)
    bot.add_task(set_ns_cri, set_ns)
    bot.add_task(block_private_cri, block_private)
    bot.add_task(list_block_private_cri, list_block_private)
    bot.add_task(unblock_private_cri, unblock_private)

    while True:
        try:
            bot.start()
        except KeyboardInterrupt:
            break
