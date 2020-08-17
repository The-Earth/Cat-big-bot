from responsive.mark import *
from responsive.misc import *
from responsive.trusted_user import *
from responsive.new_pages import *
from responsive.pm import *

from responsive import bot


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
# bot.add_query_task(button_counter_cri, button_counter)

while True:
    try:
        bot.start()
    except KeyboardInterrupt:
        break
