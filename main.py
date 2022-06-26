import multiprocessing

from components import bot
from components.mark import *
from components.misc import *
from components.new_pages import *
from components.pm import *
from components.poll import *
from components.trusted_user import *
from components.channel_helper import *
from components.show_joining import *
from components.spam_detection import *

bot.add_msg_task(get_user_id_cri, get_user_id)
bot.add_msg_task(get_chat_id_cri, get_chat_id)
bot.add_msg_task(pass_on_cri, pass_on)
bot.add_msg_task(reply_cri, reply)
bot.add_msg_task(start_cri, start)
bot.add_msg_task(mark_cri, mark)
bot.add_msg_task(list_marked_cri, list_marked)
bot.add_msg_task(unmark_cri, unmark)
bot.add_msg_task(set_trusted_cri, set_trusted)
bot.add_msg_task(list_trusted_cri, list_trusted)
bot.add_msg_task(bot_help_cri, bot_help)
bot.add_msg_task(get_permalink_cri, get_permalink)
bot.add_msg_task(list_ns_cri, list_ns)
bot.add_msg_task(start_new_pages_cri, start_new_pages)
bot.add_msg_task(stop_new_pages_cri, stop_new_pages)
bot.add_msg_task(set_ns_cri, set_ns)
bot.add_msg_task(block_private_cri, block_private)
bot.add_msg_task(list_block_private_cri, list_block_private)
bot.add_msg_task(unblock_private_cri, unblock_private)
bot.add_msg_task(set_voter_cri, set_voter)
bot.add_msg_task(list_voter_cri, list_voter)
bot.add_msg_task(unset_voter_cri, unset_voter)
bot.add_msg_task(init_poll_cri, init_poll)
bot.add_query_task(start_poll_cri, start_poll)
bot.add_query_task(abort_poll_cri, abort_poll)
bot.add_query_task(vote_cri, vote)
bot.add_query_task(stop_poll_cri, stop_poll)
bot.add_msg_task(set_channel_helper_cri, set_channel_helper)
bot.add_member_status_task(channel_helper_cri, channel_helper)
bot.add_msg_task(channel_helper_msg_deletion_cri, channel_helper_msg_deletion)
bot.add_msg_task(unset_channel_helper_cri, unset_channel_helper)
bot.add_msg_task(raw_api_cri, raw_api)
bot.add_member_status_task(show_joining_cri, show_joining)
bot.add_msg_task(set_show_joining_cri, set_show_joining)
bot.add_msg_task(unset_show_joining_cri, unset_show_joining)
bot.add_msg_task(porn_detect_tester_cri, porn_detect_tester)


def bot_run():
    while True:
        try:
            bot.start()
        except:
            pass


if __name__ == '__main__':
    multiprocessing.freeze_support()
    scheduled_stop_poll_p = multiprocessing.Process(target=stop_poll_scheduled_main, daemon=True)
    scheduled_stop_poll_p.start()
    bot_p = multiprocessing.Process(target=bot_run, daemon=True)
    bot_p.start()
    new_pages_p = multiprocessing.Process(target=new_pages_main, daemon=True)
    new_pages_p.start()
    porn_detect_p = multiprocessing.Process(target=porn_detect_main, daemon=True)
    porn_detect_p.start()

    import time
    while True:
        try:
            time.sleep(3600)
        except KeyboardInterrupt:
            break
