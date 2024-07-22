import multiprocessing
import threading

import catbot

bot = catbot.Bot(config_path='config.json')
t_lock = threading.Lock()
p_lock = multiprocessing.Lock()

from components.channel_helper import *
from components.mark import *
from components.misc import *
from components.new_pages import *
from components.pm import *
from components.poll import *
from components.show_joining import *
from components.spam_detection import *
from components.trusted_user import *
