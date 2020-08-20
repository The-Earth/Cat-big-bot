from poll import Poll

import json

import catbot
from responsive import bot, config
from responsive import record_empty_test, command_detector
from responsive import admin


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
            if voter_user.status == 'left' or voter_user.status == 'kicked':
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

    bot.send_message(msg.chat.id, text=resp_text, parse_mode='HTML', reply_to_message_id=msg.id)


@admin
def unset_voter_cri(msg: catbot.Message) -> bool:
    return command_detector('/unset_voter', msg)


def unset_voter(msg: catbot.Message):
    voter_list, rec = record_empty_test('voter', list)

    user_input_token = msg.text.split()
    rm_voter_list = []
    if msg.reply:
        rm_voter_list.append(msg.reply_to_message.from_.id)
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
