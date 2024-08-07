import time
from multiprocessing import Event

import catbot
import dateparser

from poll import Poll
from components.decorators import trusted
from components import bot, t_lock, p_lock

__all__ = [
    'set_voter',
    'list_voter',
    'unset_voter',
    'init_poll',
    'start_poll',
    'stop_poll',
    'abort_poll',
    'stop_poll_scheduled_main'
]


def get_poll_text(p: Poll) -> str:
    start_time = time.strftime('%Y/%m/%d %H:%M:%S', time.gmtime(p.start_time))
    end_time = time.strftime('%Y/%m/%d %H:%M:%S', time.gmtime(p.start_time + p.last_time))

    voted_user_set = set()
    for option in p.option_list:
        voted_user_set = voted_user_set.union(option['user'])
    total_votes = len(voted_user_set)

    voted_user_dict = {}
    chat_id = '-100' + str(p.chat_id)
    if (p.open and not p.anonymous_open) or (not p.open and not p.anonymous_closed):
        for user_id in voted_user_set:
            try:
                user = bot.get_chat_member(chat_id, user_id)
            except catbot.UserNotFoundError:
                voted_user_dict[user_id] = user_id
            else:
                voted_user_dict[user_id] = user.name

    output = bot.config['messages']['poll'].format(
        title=p.title,
        start_time=start_time,
        end_time=end_time,
        total=total_votes
    )

    for option in p.option_list:
        output += f'{option["text"]}\n'

        if (p.open and not p.anonymous_open) or (not p.open and not p.anonymous_closed):
            for user_id in option['user']:
                output += f'- {voted_user_dict[user_id]}\n'

        if (p.open and p.count_open) or (not p.open):
            proportion = len(option['user']) / total_votes if total_votes != 0 else 0
            output += f'-------- {len(option["user"])} 人 / {proportion * 100:.1f}%\n'

        output += '\n'

    return output


@trusted
def set_voter_cri(msg: catbot.Message) -> bool:
    return bot.detect_command('/set_voter', msg) and msg.chat.type != 'private'


@bot.msg_task(set_voter_cri)
def set_voter(msg: catbot.Message):
    new_voter_id = []
    if msg.reply:
        new_voter_id.append(msg.reply_to_message.from_.id)
    else:
        user_input_token = msg.text.split()
        if len(user_input_token) == 1:
            bot.send_message(msg.chat.id, text=bot.config['messages']['set_voter_prompt'], reply_to_message_id=msg.id)
            return
        else:
            for item in user_input_token[1:]:
                try:
                    new_voter_id.append(int(item))
                except ValueError:
                    continue
    with t_lock:
        if 'voter' in bot.record:
            voter_dict = bot.record['voter']
        else:
            voter_dict = {}
        if str(msg.chat.id) not in voter_dict.keys():
            voter_dict[str(msg.chat.id)] = []
        voter_set = set(voter_dict[str(msg.chat.id)])
        old_voter_set = voter_set.copy()
        voter_set.update(new_voter_id)
        delta = voter_set - old_voter_set
        if len(delta) == 0:
            bot.send_message(msg.chat.id, text=bot.config['messages']['set_voter_failed'], reply_to_message_id=msg.id)
        else:
            reply_text = bot.config['messages']['set_voter_succ']
            for item in delta:
                reply_text += str(item) + '\n'

            voter_dict[str(msg.chat.id)] = list(voter_set)
            bot.record['voter'] = voter_dict
            bot.send_message(msg.chat.id, text=reply_text, reply_to_message_id=msg.id)


@trusted
def list_voter_cri(msg: catbot.Message) -> bool:
    return bot.detect_command('/list_voter', msg) and msg.chat.type != 'private'


@bot.msg_task(list_voter_cri)
def list_voter(msg: catbot.Message):
    resp_list = []
    bot.api('sendChatAction', {'chat_id': msg.chat.id, 'action': 'typing'})
    with t_lock:
        if 'voter' in bot.record:
            voter_dict = bot.record['voter']
        else:
            voter_dict = {}
        if str(msg.chat.id) in voter_dict.keys():
            for voter_id in voter_dict[str(msg.chat.id)]:
                try:
                    voter_user = bot.get_chat_member(msg.chat.id, voter_id)
                    if voter_user.status == 'kicked':
                        continue
                except catbot.UserNotFoundError:
                    continue
                else:
                    resp_list.append(voter_user)

    resp_text: str = bot.config['messages']['list_voter_succ']
    for user in resp_list:
        resp_text += f'{user.name}、'
    resp_text = resp_text.rstrip('、')
    if len(resp_list) == 0:
        resp_text = bot.config['messages']['list_voter_empty']

    bot.send_message(msg.chat.id, text=resp_text, reply_to_message_id=msg.id)


@trusted
def unset_voter_cri(msg: catbot.Message) -> bool:
    return bot.detect_command('/unset_voter', msg)


@bot.msg_task(unset_voter_cri)
def unset_voter(msg: catbot.Message):
    with t_lock:
        if 'voter' in bot.record:
            voter_dict = bot.record['voter']
        else:
            voter_dict = {}

        user_input_token = msg.text.split()
        rm_voter_list = []
        if msg.reply:
            rm_voter_list.append(str(msg.reply_to_message.from_.id))
            if msg.reply_to_message.from_.id in voter_dict[str(msg.chat.id)]:
                voter_dict[str(msg.chat.id)].remove(msg.reply_to_message.from_.id)
            else:
                bot.send_message(
                    msg.chat.id,
                    text=bot.config['messages']['unset_voter_failed'],
                    reply_to_message_id=msg.id
                )
                return
        else:
            if len(user_input_token) == 1:
                bot.send_message(msg.chat.id, text=bot.config['messages']['unset_voter_prompt'],
                                 reply_to_message_id=msg.id)
                return
            else:
                for item in user_input_token[1:]:
                    try:
                        voter_dict[str(msg.chat.id)].remove(int(item))
                    except ValueError:
                        continue
                    else:
                        rm_voter_list.append(item)

        if len(rm_voter_list) == 0:
            bot.send_message(msg.chat.id, text=bot.config['messages']['unset_voter_failed'], reply_to_message_id=msg.id)
        else:
            bot.record['voter'] = voter_dict
            resp_text = bot.config['messages']['unset_voter_succ'] + '\n'.join(rm_voter_list)
            bot.send_message(msg.chat.id, text=resp_text, reply_to_message_id=msg.id)


@trusted
def init_poll_cri(msg: catbot.Message) -> bool:
    return bot.detect_command('/init_poll', msg) and msg.chat.type != 'private'


@bot.msg_task(init_poll_cri)
def init_poll(msg: catbot.Message):
    user_input_token = msg.html_formatted_text.split()
    if len(user_input_token) == 1:
        bot.send_message(msg.chat.id, text=bot.config['messages']['init_poll_failed'], reply_to_message_id=msg.id)
        return
    poll_chat_id = int(str(msg.chat.id).replace('-100', ''))
    p = Poll(poll_chat_id, msg.id)

    i = 1

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
            p.last_time = dateparser.parse(t_str, settings={'PREFER_DATES_FROM': 'future'}).timestamp() - time.time()
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
        elif user_input_token[i] == '-p':
            i += 1
            while i < len(user_input_token) and not user_input_token[i].startswith('-'):
                try:
                    p.privilege_level = int(user_input_token[i])
                except ValueError:
                    bot.send_message(msg.chat.id, text=bot.config['messages']['init_poll_failed'],
                                     reply_to_message_id=msg.id)
                    return
                else:
                    i += 1
                    break
        else:  # format error
            bot.send_message(msg.chat.id, text=bot.config['messages']['init_poll_failed'], reply_to_message_id=msg.id)
            return

    if len(p.option_list) == 0:
        bot.send_message(msg.chat.id, text=bot.config['messages']['init_poll_failed'], reply_to_message_id=msg.id)
        return

    with t_lock:
        if 'poll' in bot.record:
            poll_list = bot.record['poll']
        else:
            poll_list = []
        poll_list.append(p.to_json())
        bot.record['poll'] = poll_list

    resp_text = bot.config['messages']['init_poll_succ'].format(
        title=p.title,
        last=p.readable_time,
        anon_open=p.anonymous_open,
        anon_closed=p.anonymous_closed,
        count_open=p.count_open,
        multiple=p.multiple,
        privilege=bot.config['messages']['vote_privilege'][str(p.privilege_level)]
    )
    start_button = catbot.InlineKeyboardButton(bot.config['messages']['start_poll_button'],
                                               callback_data=f'vote_{p.chat_id}_{p.init_id}_start')
    abort_button = catbot.InlineKeyboardButton(bot.config['messages']['abort_poll_button'],
                                               callback_data=f'vote_{p.chat_id}_{p.init_id}_abort')
    keyboard = catbot.InlineKeyboard([[start_button, abort_button]])
    bot.send_message(msg.chat.id, text=resp_text, reply_to_message_id=msg.id, reply_markup=keyboard, parse_mode='HTML')


@trusted
def start_poll_cri(query: catbot.CallbackQuery) -> bool:
    return query.data.startswith('vote_') and query.data.endswith('_start')


@bot.query_task(start_poll_cri)
def start_poll(query: catbot.CallbackQuery):
    data_token = query.data.split('_')
    try:
        cmd_chat_id = int(data_token[1])
        cmd_id = int(data_token[2])
    except ValueError:
        bot.answer_callback_query(query.id)
        return

    with t_lock:
        if 'poll' in bot.record:
            poll_list = bot.record['poll']
        else:
            poll_list = []

        for i in range(len(poll_list)):
            p = Poll.from_json(poll_list[i])
            if p.chat_id == cmd_chat_id and p.init_id == cmd_id:
                break
        else:
            bot.answer_callback_query(query.id, text=bot.config['messages']['start_poll_not_found'])
            return

        p.start()

        button_list = []
        for j in range(len(p.option_list)):
            option = p.option_list[j]
            button_list.append([catbot.InlineKeyboardButton(option['text'],
                                                            callback_data=f'vote_{p.chat_id}_{p.init_id}_{j}')])
        button_list.append([catbot.InlineKeyboardButton(bot.config['messages']['stop_poll_button'],
                                                        callback_data=f'vote_{p.chat_id}_{p.init_id}_stop')])
        keyboard = catbot.InlineKeyboard(button_list)

        poll_msg: catbot.Message = bot.send_message(query.msg.chat.id, text=get_poll_text(p), reply_markup=keyboard,
                                                    reply_to_message_id=query.msg.id, parse_mode='HTML')
        bot.edit_message(query.msg.chat.id, query.msg.id, text=query.msg.html_formatted_text, parse_mode='HTML')
        bot.answer_callback_query(query.id, text=bot.config['messages']['start_poll_answer'])

        p.poll_id = poll_msg.id
        poll_list[i] = p.to_json()
        bot.record['poll'] = poll_list


@trusted
def abort_poll_cri(query: catbot.CallbackQuery) -> bool:
    return query.data.startswith('vote_') and query.data.endswith('_abort')


@bot.query_task(abort_poll_cri)
def abort_poll(query: catbot.CallbackQuery):
    data_token = query.data.split('_')
    try:
        cmd_chat_id = int(data_token[1])
        cmd_id = int(data_token[2])
    except ValueError:
        bot.answer_callback_query(query.id)
        return

    with t_lock:
        if 'poll' in bot.record:
            poll_list = bot.record['poll']
        else:
            poll_list = []
        for i in range(len(poll_list)):
            p = Poll.from_json(poll_list[i])
            if p.chat_id == cmd_chat_id and p.init_id == cmd_id:
                poll_list.pop(i)
                break
        else:
            bot.answer_callback_query(query.id, text=bot.config['messages']['start_poll_not_found'])
            return

        bot.record['poll'] = poll_list

    bot.edit_message(
        query.msg.chat.id,
        query.msg.id,
        text=bot.config['messages']['abort_poll_title'] + query.msg.html_formatted_text, parse_mode='HTML'
    )
    bot.answer_callback_query(query.id, text=bot.config['messages']['abort_poll_answer'])


def vote_cri(query: catbot.CallbackQuery) -> bool:
    return query.data.startswith('vote_') and not (query.data.endswith('_stop') or query.data.endswith('_start')
                                                   or query.data.endswith('_abort'))


@bot.query_task(vote_cri)
def vote(query: catbot.CallbackQuery):
    callback_token = query.data.split('_')
    if 'voter' in bot.record:
        voter_dict = bot.record['voter']
    else:
        voter_dict = {}
    if 'trusted' in bot.record:
        trusted_list = bot.record['trusted']
    else:
        trusted_list = {}
    ac_list = bot.secure_record_fetch('ac', list, file=bot.config['ac_record'])[0]

    if str(query.msg.chat.id) in voter_dict.keys():
        voter_list = voter_dict[str(query.msg.chat.id)] + trusted_list
    else:
        voter_list = trusted_list

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

    with t_lock:
        if 'poll' in bot.record:
            poll_list = bot.record['poll']
        else:
            poll_list = []

        for i in range(len(poll_list)):
            p = Poll.from_json(poll_list[i])

            if p.chat_id == callback_chat_id and p.init_id == callback_init_id and p.open:
                # privilege check
                if p.privilege_level == 1 and query.from_.id not in voter_list:
                    bot.answer_callback_query(query.id, text=bot.config['messages']['vote_ineligible'])
                    return
                if p.privilege_level == 2 and query.from_.id not in voter_list:
                    for user in ac_list:
                        if user['telegram_id'] == query.from_.id and not user['confirmed']:
                            bot.answer_callback_query(query.id, text=bot.config['messages']['vote_ineligible'])
                            return
                        if user['telegram_id'] == query.from_.id and user['confirmed']:
                            break
                    else:
                        bot.answer_callback_query(query.id, text=bot.config['messages']['vote_ineligible'])
                        return

                p.vote(query.from_.id, choice)

                poll_list[i] = p.to_json()
                bot.record['poll'] = poll_list
                break

            elif p.chat_id == callback_chat_id and p.init_id == callback_init_id and not p.open:
                bot.answer_callback_query(query.id, text=bot.config['messages']['vote_poll_stopped'], show_alert=True)
                return

        bot.answer_callback_query(query.id, text=bot.config['messages']['vote_received'], show_alert=True)
        button_list = []
        for j in range(len(p.option_list)):
            option = p.option_list[j]
            button_list.append([catbot.InlineKeyboardButton(
                option['text'],
                callback_data=f'vote_{p.chat_id}_{p.init_id}_{j}'
            )])
        button_list.append([catbot.InlineKeyboardButton(
            bot.config['messages']['stop_poll_button'],
            callback_data=f'vote_{p.chat_id}_{p.init_id}_stop'
        )])
        keyboard = catbot.InlineKeyboard(button_list)

        bot.edit_message(
            '-100' + str(callback_chat_id),
            p.poll_id, text=get_poll_text(p),
            reply_markup=keyboard, parse_mode='HTML'
        )


@trusted
def stop_poll_cri(query: catbot.CallbackQuery) -> bool:
    return query.data.startswith('vote') and query.data.endswith('_stop')


@bot.query_task(stop_poll_cri)
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

    with t_lock:
        if 'poll' in bot.record:
            poll_list = bot.record['poll']
        else:
            poll_list = []
        for i in range(len(poll_list)):
            p = Poll.from_json(poll_list[i])

            if p.chat_id == callback_chat_id and p.init_id == callback_init_id and p.open:
                p.stop()
                poll_list.pop(i)
                bot.record['poll'] = poll_list

                bot.answer_callback_query(query.id)
                resp_text = bot.config['messages']['stop_poll_title']
                bot.edit_message(
                    '-100' + str(callback_chat_id),
                    p.poll_id,
                    text=resp_text + get_poll_text(p),
                    parse_mode='HTML'
                )
                break


def stop_poll_scheduled():
    with p_lock:
        if 'poll' in bot.record:
            poll_list = bot.record['poll']
        else:
            poll_list = []

        i = 0
        while i < (len(poll_list)):
            p = Poll.from_json(poll_list[i])
            if time.time() > p.end_time and p.open:
                p.stop()
                poll_list.pop(i)
                bot.record['poll'] = poll_list

                bot.send_message(
                    '-100' + str(p.chat_id),
                    text=bot.config['messages']['stop_poll_scheduled'].format(title=p.title),
                    parse_mode='HTML', reply_to_message_id=p.poll_id
                )
                resp_text = bot.config['messages']['stop_poll_title']
                bot.edit_message(
                    '-100' + str(p.chat_id),
                    p.poll_id, text=resp_text + get_poll_text(p),
                    parse_mode='HTML'
                )
            else:
                i += 1


def stop_poll_scheduled_main(event: Event):
    while not event.is_set():
        stop_poll_scheduled()
        time.sleep(60)
