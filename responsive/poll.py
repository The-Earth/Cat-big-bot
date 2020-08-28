import json
import time

import parsedatetime

import catbot
from poll import Poll
from responsive import admin
from responsive import bot, config, t_lock, p_lock
from responsive import record_empty_test, command_detector


def get_poll_text(p: Poll) -> str:
    start_time = time.strftime('%Y/%m/%d %H:%M:%S', time.gmtime(p.start_time))
    end_time = time.strftime('%Y/%m/%d %H:%M:%S', time.gmtime(p.start_time + p.last_time))
    total_votes = 0
    for option in p.option_list:
        total_votes += len(option['user'])

    chat_id = '-100' + str(p.chat_id)
    output = config['messages']['poll'].format(title=p.title, start_time=start_time, end_time=end_time,
                                               total=total_votes)

    for option in p.option_list:
        output += f'{option["text"]}\n'

        if (p.open and not p.anonymous_open) or (not p.open and not p.anonymous_closed):
            for user_id in option['user']:
                try:
                    user = bot.get_chat_member(chat_id, user_id)
                except catbot.UserNotFoundError:
                    output += f'- {user_id}\n'
                else:
                    output += f'- {user.name}\n'

        if (p.open and p.count_open) or (not p.open):
            proportion = len(option['user']) / total_votes if total_votes != 0 else 0
            output += f'-------- {len(option["user"])} {proportion * 100:.2f}%\n'

        output += '\n'

    return output


@admin
def set_voter_cri(msg: catbot.Message) -> bool:
    return command_detector('/set_voter', msg)


def set_voter(msg: catbot.Message):
    voter_list, rec = record_empty_test('voter', list)

    new_voter_id = []
    if msg.reply:
        new_voter_id.append(msg.reply_to_message.from_.id)
    else:
        user_input_token = msg.text.split()
        if len(user_input_token) == 1:
            bot.send_message(msg.chat.id, text=config['messages']['set_voter_prompt'], reply_to_message_id=msg.id)
            return
        else:
            for item in user_input_token[1:]:
                try:
                    new_voter_id.append(int(item))
                except ValueError:
                    continue

    voter_set = set(voter_list)
    old_voter_set = voter_set.copy()
    voter_set.update(new_voter_id)
    delta = voter_set - old_voter_set
    if len(delta) == 0:
        bot.send_message(msg.chat.id, text=config['messages']['set_voter_failed'], reply_to_message_id=msg.id)
    else:
        reply_text = config['messages']['set_voter_succ']
        for item in delta:
            reply_text += str(item) + '\n'

        rec['voter'] = list(voter_set)
        json.dump(rec, open(config['record'], 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
        bot.send_message(msg.chat.id, text=reply_text, reply_to_message_id=msg.id)


@admin
def list_voter_cri(msg: catbot.Message) -> bool:
    return command_detector('/list_voter', msg) and msg.chat.type != 'private'


def list_voter(msg: catbot.Message):
    voter_list, rec = record_empty_test('voter', list)

    resp_list = []
    bot.send_message(msg.chat.id, text=config['messages']['list_user_pre'], reply_to_message_id=msg.id)
    for voter_id in voter_list:
        try:
            voter_user = bot.get_chat_member(msg.chat.id, voter_id)
            if voter_user.status == 'kicked':
                continue
        except catbot.UserNotFoundError:
            continue
        else:
            resp_list.append(voter_user)

    resp_text: str = config['messages']['list_voter_succ']
    for user in resp_list:
        resp_text += f'{user.name}、'
    resp_text = resp_text.rstrip('、')
    if len(resp_list) == 0:
        resp_text = config['messages']['list_voter_empty']

    bot.send_message(msg.chat.id, text=resp_text, reply_to_message_id=msg.id)


@admin
def unset_voter_cri(msg: catbot.Message) -> bool:
    return command_detector('/unset_voter', msg)


def unset_voter(msg: catbot.Message):
    voter_list, rec = record_empty_test('voter', list)

    user_input_token = msg.text.split()
    rm_voter_list = []
    if msg.reply:
        rm_voter_list.append(str(msg.reply_to_message.from_.id))
        if msg.reply_to_message.from_.id in voter_list:
            voter_list.remove(msg.reply_to_message.from_.id)
        else:
            bot.send_message(msg.chat.id, text=config['messages']['unset_voter_failed'], reply_to_message_id=msg.id)
            return
    else:
        if len(user_input_token) == 1:
            bot.send_message(msg.chat.id, text=config['messages']['unset_voter_prompt'],
                             reply_to_message_id=msg.id)
            return
        else:
            for item in user_input_token[1:]:
                try:
                    voter_list.remove(int(item))
                except ValueError:
                    continue
                else:
                    rm_voter_list.append(item)

    if len(rm_voter_list) == 0:
        bot.send_message(msg.chat.id, text=config['messages']['unset_voter_failed'], reply_to_message_id=msg.id)
    else:
        rec['voter'] = voter_list
        json.dump(rec, open(config['record'], 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
        resp_text = config['messages']['unset_voter_succ'] + '\n'.join(rm_voter_list)
        bot.send_message(msg.chat.id, text=resp_text, reply_to_message_id=msg.id)


@admin
def init_poll_cri(msg: catbot.Message) -> bool:
    return command_detector('/init_poll', msg) and msg.chat.type != 'private'


def init_poll(msg: catbot.Message):
    poll_list, rec = record_empty_test('poll', list)
    user_input_token = msg.text.split()
    if len(user_input_token) == 1:
        bot.send_message(msg.chat.id, text=config['messages']['init_poll_failed'], reply_to_message_id=msg.id)
        return
    poll_chat_id = int(str(msg.chat.id).replace('-100', ''))
    p = Poll(poll_chat_id, msg.id)

    i = 1
    parser = parsedatetime.Calendar()
    while i < len(user_input_token):
        if user_input_token[i] == '-n':
            i += 1
            title_list = []
            while i < len(user_input_token) and not user_input_token[i].startswith('-'):
                title_list.append(user_input_token[i])
                i += 1
            p.title = ' '.join(title_list)

        elif user_input_token[i] == '-t':
            i += 1
            t_list = []
            while i < len(user_input_token) and not user_input_token[i].startswith('-'):
                t_list.append(user_input_token[i])
                i += 1
            t_str = ' '.join(t_list)
            p.last_time = time.mktime(parser.parse(datetimeString=t_str)[0]) - time.time()
            p.readable_time = t_str

        elif user_input_token[i] == '-o':
            i += 1
            option_text = ''
            while i < len(user_input_token) and not user_input_token[i].startswith('-'):
                option_text += user_input_token[i] + ' '
                i += 1
            options = option_text.split('!')
            for j in range(options.count('')):
                options.remove('')
            p.set_option(options)

        elif user_input_token[i] == '-ao':
            p.anonymous_open = True
            i += 1
        elif user_input_token[i] == '-ac':
            p.anonymous_closed = True
            i += 1
        elif user_input_token[i] == '-c':
            p.count_open = True
            i += 1
        elif user_input_token[i] == '-m':
            p.multiple = True
            i += 1
        else:  # format error
            bot.send_message(msg.chat.id, text=config['messages']['init_poll_failed'], reply_to_message_id=msg.id)
            return

    if len(p.option_list) == 0:
        bot.send_message(msg.chat.id, text=config['messages']['init_poll_failed'], reply_to_message_id=msg.id)
        return

    poll_list.append(p.to_json())
    rec['poll'] = poll_list
    json.dump(rec, open(config['record'], 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
    resp_text = config['messages']['init_poll_succ'].format(poll_id=f'{p.chat_id}_{p.init_id}',
                                                            title=p.title,
                                                            last=p.readable_time,
                                                            anon_open=p.anonymous_open,
                                                            anon_closed=p.anonymous_closed,
                                                            count_open=p.count_open,
                                                            multiple=p.multiple)
    bot.send_message(msg.chat.id, text=resp_text, reply_to_message_id=msg.id)


@admin
def start_poll_cri(msg: catbot.Message):
    if len(msg.commands) == 0 or not msg.text.startswith('/start_poll_'):
        return False
    cmd_token = msg.commands[0].split('_')
    return len(cmd_token) == 4


def start_poll(msg: catbot.Message):
    poll_list, rec = record_empty_test('poll', list)
    cmd_token = msg.commands[0].replace(f'@{bot.username}', '').split('_')
    try:
        cmd_chat_id = int(cmd_token[2])
        cmd_id = int(cmd_token[3])
    except ValueError:
        return

    if cmd_token[2] != str(msg.chat.id).replace('-100', ''):
        bot.send_message(msg.chat.id, text=config['messages']['start_poll_not_found'], reply_to_message_id=msg.id)
        return
    for i in range(len(poll_list)):
        p = Poll.from_json(poll_list[i])
        if p.chat_id == cmd_chat_id and p.init_id == cmd_id:
            break
    else:
        bot.send_message(msg.chat.id, text=config['messages']['start_poll_not_found'], reply_to_message_id=msg.id)
        return

    if p.open or p.start_time != 0:
        url = f'{msg.chat.link}/{p.poll_id}'
        bot.send_message(msg.chat.id, text=config['messages']['start_poll_already'].format(url=url),
                         reply_to_message_id=msg.id)
        return

    p.start()

    button_list = []
    for j in range(len(p.option_list)):
        option = p.option_list[j]
        button_list.append([catbot.InlineKeyboardButton(option['text'],
                                                        callback_data=f'vote_{p.chat_id}_{p.init_id}_{j}')])
    button_list.append([catbot.InlineKeyboardButton(config['messages']['stop_poll_button'],
                                                    callback_data=f'vote_{p.chat_id}_{p.init_id}_stop')])
    keyboard = catbot.InlineKeyboard(button_list)

    poll_msg: catbot.Message = bot.send_message(msg.chat.id, text=get_poll_text(p), reply_markup=keyboard,
                                                reply_to_message_id=msg.id)

    p.poll_id = poll_msg.id
    poll_list[i] = p.to_json()
    rec['poll'] = poll_list
    json.dump(rec, open(config['record'], 'w', encoding='utf-8'), indent=2, ensure_ascii=False)


def vote_cri(query: catbot.CallbackQuery) -> bool:
    return query.data.startswith('vote_') and not query.data.endswith('_stop')


def vote(query: catbot.CallbackQuery):
    callback_token = query.data.split('_')
    voter_list = record_empty_test('voter', list)[0]
    if query.from_.id not in voter_list:
        bot.answer_callback_query(query.id, text=config['messages']['vote_ineligible'])
        return
    if not len(callback_token) == 4:
        bot.answer_callback_query(query.id)
        return
    try:
        callback_chat_id = int(query.data.split('_')[1])
        callback_init_id = int(query.data.split('_')[2])
        choice = int(query.data.split('_')[3])
    except ValueError:
        bot.answer_callback_query(query.id)
        return

    t_lock.acquire()
    poll_list, rec = record_empty_test('poll', list)
    for i in range(len(poll_list)):
        p = Poll.from_json(poll_list[i])

        if p.chat_id == callback_chat_id and p.init_id == callback_init_id and p.open:
            p.vote(query.from_.id, choice)

            poll_list[i] = p.to_json()
            rec['poll'] = poll_list
            json.dump(rec, open(config['record'], 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
            t_lock.release()

            bot.answer_callback_query(query.id, text=config['messages']['vote_received'], show_alert=True)
            button_list = []
            for j in range(len(p.option_list)):
                option = p.option_list[j]
                button_list.append([catbot.InlineKeyboardButton(option['text'],
                                                                callback_data=f'vote_{p.chat_id}_{p.init_id}_{j}')])
            button_list.append([catbot.InlineKeyboardButton(config['messages']['stop_poll_button'],
                                                            callback_data=f'vote_{p.chat_id}_{p.init_id}_stop')])
            keyboard = catbot.InlineKeyboard(button_list)

            bot.edit_message('-100' + str(callback_chat_id), p.poll_id, text=get_poll_text(p),
                             reply_markup=keyboard)
            break

        elif p.chat_id == callback_chat_id and p.init_id == callback_init_id and not p.open:
            bot.answer_callback_query(query.id, text=config['messages']['vote_poll_stopped'], show_alert=True)
            t_lock.release()
            break

    else:
        t_lock.release()


@admin
def stop_poll_cri(query: catbot.CallbackQuery) -> bool:
    return query.data.startswith('vote') and query.data.endswith('_stop')


def stop_poll(query: catbot.CallbackQuery):
    callback_token = query.data.split('_')
    if not len(callback_token) == 4:
        bot.answer_callback_query(query.id)
        return
    try:
        callback_chat_id = int(query.data.split('_')[1])
        callback_init_id = int(query.data.split('_')[2])
    except ValueError:
        bot.answer_callback_query(query.id)
        return

    t_lock.acquire()
    poll_list, rec = record_empty_test('poll', list)
    for i in range(len(poll_list)):
        p = Poll.from_json(poll_list[i])

        if p.chat_id == callback_chat_id and p.init_id == callback_init_id and p.open:
            poll_list.pop(i)
            rec['poll'] = poll_list
            json.dump(rec, open(config['record'], 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
            t_lock.release()

            bot.answer_callback_query(query.id)
            resp_text = config['messages']['stop_poll_title']
            bot.edit_message('-100' + str(callback_chat_id), p.poll_id,
                             text=resp_text + get_poll_text(p))
            break
    else:
        t_lock.release()


def stop_poll_scheduled():
    p_lock.acquire()
    poll_list, rec = record_empty_test('poll', list)

    i = 0
    while i < (len(poll_list)):
        p = Poll.from_json(poll_list[i])
        if time.time() > p.end_time and p.open:
            poll_list.pop(i)
            rec['poll'] = poll_list
            json.dump(rec, open(config['record'], 'w', encoding='utf-8'), indent=2, ensure_ascii=False)

            chat_link = bot.get_chat('-100' + str(p.chat_id)).link
            poll_link = chat_link + f'/{p.poll_id}' if chat_link != '' else ''
            bot.send_message('-100' + str(p.chat_id),
                             text=config['messages']['stop_poll_scheduled'].format(title=p.title, link=poll_link))
            resp_text = config['messages']['stop_poll_title']
            bot.edit_message('-100' + str(p.chat_id), p.poll_id,
                             text=resp_text + get_poll_text(p))

        i += 1

    p_lock.release()


def stop_poll_scheduled_main():
    while True:
        stop_poll_scheduled()
        time.sleep(60)
