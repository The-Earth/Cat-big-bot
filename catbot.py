import requests


class User:
    def __init__(self, user_json: dict):
        self.raw = user_json
        self.id: int = user_json['id']
        self.is_bot: bool = user_json['is_bot']
        if 'last_name' in user_json:
            self.name = f"{user_json['first_name']} {user_json['last_name']}"
        else:
            self.name = user_json['first_name']
        if 'username' in user_json:
            self.username: str = user_json['username']
            self.link = 't.me/' + self.username
        else:
            self.username = ''
            self.link = ''


class Bot(User):
    def __init__(self, config: dict):
        self.config = config
        self.token: str = self.config['token']
        self.base_url = 'https://api.telegram.org/bot' + self.token + '/'

        if 'proxy' in self.config and self.config['proxy']['enable']:
            self.proxy_kw = {'proxies': {'https': self.config['proxy']['proxy_url']}}
        else:
            self.proxy_kw = {}
        get_me_resp: dict = requests.get(self.base_url + 'getMe', **self.proxy_kw).json()

        if not get_me_resp['ok']:
            raise APIError('Bot initialization failed.' + get_me_resp['description'])

        super().__init__(get_me_resp['result'])

        self.can_join_groups: bool = get_me_resp['result']['can_join_groups']
        self.can_read_all_group_messages: bool = get_me_resp['result']['can_read_all_group_messages']
        self.supports_inline_queries: bool = get_me_resp['result']['supports_inline_queries']

        self.tasks = []

    def api(self, action: str, data: dict):
        resp = requests.post(self.base_url + action, data=data, **self.proxy_kw).json()
        if not resp['ok']:
            raise APIError(f'API request "{action}" failed. {resp["description"]}')

        return resp['result']

    def get_updates(self, offset: int=0, timeout: int=60) -> list:
        update_data = {'offset': offset,
                       'timeout': timeout}

        return self.api('getUpdates', update_data)

    def add_task(self, criteria, action, **action_kw):
        """
        :param criteria:
            A function that lead flow of program into "action" function. It should take a Message-like object as the
            only argument and returns a bool. When it returns True, "action" will be executed. An example is to return
            True if the message starts with "/start", which is the standard starting of private chats with users.
        :param action:
            A function to be executed when criteria returns True. Typically it's the response on users' actions.
            It should take a Message-like object as the only positional argument and accept keyword arguments. Arguments
            in action_kw will be passed to it.
        :param action_kw:
            Keyword arguments that will be passed to action when it is called.
        :return:
        """
        self.tasks.append((criteria, action, action_kw))

    def start(self):
        update_offset = 0
        while True:
            updates = self.get_updates(update_offset)
            for item in updates:
                update_offset = item['update_id'] + 1
                if 'message' in item.keys():
                    msg = Message(item['message'])
                elif 'edited_message' in item.keys():
                    msg = Message(item['edited_message'])
                else:
                    continue

                for criteria, action, action_kw in self.tasks:
                    if criteria(msg):
                        action(msg, **action_kw)

    def send_message(self, chat_id, **kw):
        """
        :param chat_id: Unique identifier for the target chat or username of the target channel
        :param kw: Keyword arguments defined in Telegram bot api. See https://core.telegram.org/bots/api#sendmessage
            General keywords:
                - parse_mode: Optional. Should be one of MarkdownV2 or HTML or Markdown.
                - disable_web_page_preview: Optional. Should be True or False. Disables link previews for links
                                            in this message.
                - disable_notification: Optional. Should be True or False. Sends the message silently. Users will
                                        receive a notification with no sound.
                - reply_to_message_id: Optional. If the message is a reply, ID of the original message.
            For plain text messages:
                - text: Text of the message to be sent, 1-4096 characters after entities parsing.
        :return:
        """
        msg_kw = {'chat_id': chat_id, **kw}
        return self.api('sendMessage', msg_kw)


class Message:
    def __init__(self, msg_json: dict):
        self.raw = msg_json
        self.chat = Chat(msg_json['chat'])
        self.id: int = msg_json['message_id']
        self.from_ = User(msg_json['from'])
        self.date: int = msg_json['date']

        if 'forward_from' in msg_json.keys():
            # forwarded from users who allowed a link to their account in forwarded message
            self.forward_from = User(msg_json['forward_from'])
            self.forward = True
        elif 'forward_sender_name' in msg_json.keys():
            # forwarded from users who disallowed a link to their account in forwarded message
            self.forward_sender_name: str = msg_json['forward_sender_name']
            self.forward = True
        elif 'forward_from_chat' in msg_json.keys():
            # forwarded from channels
            self.forward_from_chat = Chat(msg_json['forward_from_chat'])
            self.forward_from_message_id: int = msg_json['forward_from_message_id']
            self.forward_signature: str = msg_json['forward_signature']
            self.forward = True
        else:
            self.forward = False

        if self.forward:
            self.forward_date: int = msg_json['forward_date']

        if 'reply_to_message' in msg_json.keys():
            self.reply_to_message = Message(msg_json['reply_to_message'])
            self.reply = True
        else:
            self.reply = False

        if 'edit_date' in msg_json.keys():
            self.edit_date: int = msg_json['edit_date']
            self.edit = True
        else:
            self.edit = False

        if 'text' in msg_json.keys():
            self.text: str = msg_json['text']
        elif 'caption' in msg_json.keys():
            self.text: str = msg_json['caption']
        else:
            self.text: str = ''

        self.mentions = []
        self.hashtags = []
        self.cashtags = []
        self.commands = []
        self.links = []
        self.bolds = []
        self.italics = []
        self.underlines = []
        self.strikethroughs = []
        self.codes = []
        self.text_links = []
        self.text_mention = []
        if 'entities' in msg_json.keys() or 'caption_entities' in msg_json.keys():
            entity_type = 'entities' if 'entities' in msg_json.keys() else 'caption_entities'
            for item in msg_json[entity_type]:
                offset = item['offset']
                length = item['length']
                if item['type'] == 'mention':
                    self.mentions.append(self.text[offset:offset + length])
                elif item['type'] == 'hashtag':
                    self.hashtags.append(self.text[offset:offset + length])
                elif item['type'] == 'cashtag':
                    self.cashtags.append(self.text[offset:offset + length])
                elif item['type'] == 'bot_command':
                    self.commands.append(self.text[offset:offset + length])
                elif item['type'] == 'url':
                    self.links.append(self.text[offset:offset + length])
                elif item['type'] == 'bold':
                    self.bolds.append(self.text[offset:offset + length])
                elif item['type'] == 'italic':
                    self.italics.append(self.text[offset:offset + length])
                elif item['type'] == 'underline':
                    self.underlines.append(self.text[offset:offset + length])
                elif item['type'] == 'strikethrough':
                    self.strikethroughs.append(self.text[offset:offset + length])
                elif item['type'] == 'code':
                    self.codes.append(self.text[offset:offset + length])
                elif item['type'] == 'text_link':
                    self.text_links.append((self.text[offset:offset + length], item['url']))
                elif item['type'] == 'text_mention':
                    self.text_mention.append((self.text[offset:offset + length], User(item['user'])))

        if 'dice' in msg_json.keys():
            self.dice = True
            self.dice_emoji = msg_json['dice']['emoji']
            self.dice_value = msg_json['dice']['value']
        else:
            self.dice = False

    def __str__(self):
        return self.raw


class Chat:
    def __init__(self, chat_json: dict):
        self.raw = chat_json
        self.id: int = chat_json['id']
        self.type: str = chat_json['type']

        if self.type == 'supergroup' or self.type == 'group' or self.type == 'channel':
            self.name: str = chat_json['title']
        else:
            if 'last_name' in chat_json.keys():
                self.name = f'{chat_json["first_name"]} {chat_json["last_name"]}'
            else:
                self.name = chat_json['first_name']

        if 'username' in chat_json.keys() and self.type != 'private':
            self.username: str = chat_json['username']
            self.link = 't.me/' + self.username
        else:
            self.username = ''
            self.link = ''

    def __str__(self):
        return self.raw


class APIError(Exception):
    pass
