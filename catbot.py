import threading
from typing import List, Dict

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

        self.msg_tasks = []
        self.query_tasks = []

    def api(self, action: str, data: dict):
        resp = requests.post(self.base_url + action, json=data, **self.proxy_kw).json()
        if not resp['ok']:
            raise APIError(f'API request "{action}" failed. {resp["description"]}')

        return resp['result']

    def get_updates(self, offset: int = 0, timeout: int = 60) -> list:
        update_data = {'offset': offset,
                       'timeout': timeout}
        updates = self.api('getUpdates', update_data)
        print(updates)
        return updates

    def add_msg_task(self, criteria, action, **action_kw):
        """
        Add tasks for the bot to process. For message updates only. Use add_query_task for callback query updates.
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
        self.msg_tasks.append((criteria, action, action_kw))

    def add_query_task(self, criteria, action, **action_kw):
        """
        Similar to add_msg_task, which add criteria and action for callback queries, typically clicks from
        in-message buttons (I would like to call them in-message instead of inline, which is used by Telegram).
        """
        self.query_tasks.append((criteria, action, action_kw))

    def start(self):
        update_offset = 0
        while True:
            try:
                updates = self.get_updates(update_offset)
            except APIError as e:
                print(e.args[0])
                continue

            for item in updates:
                update_offset = item['update_id'] + 1
                if 'message' in item.keys() or 'edited_message' in item.keys():
                    msg_type = 'message' if 'message' in item.keys() else 'edited_message'
                    msg = Message(item[msg_type])
                    for criteria, action, action_kw in self.msg_tasks:
                        if criteria(msg):
                            threading.Thread(target=action, args=(msg,), kwargs=action_kw).start()

                elif 'callback_query' in item.keys():
                    query = CallbackQuery(item['callback_query'])
                    if not hasattr(query, 'msg'):
                        continue
                    for criteria, action, action_kw in self.query_tasks:
                        if criteria(query):
                            threading.Thread(target=action, args=(query,), kwargs=action_kw).start()

                else:
                    continue

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
                - reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard,
                                custom reply keyboard, instructions to remove reply keyboard or to force a reply
                                from the user. A common content of this param is an InlineKeyboard object.
        :return:
        """
        if 'reply_markup' in kw.keys():
            kw['reply_markup'] = kw['reply_markup'].parse()

        msg_kw = {'chat_id': chat_id, **kw}
        return Message(self.api('sendMessage', msg_kw))

    def edit_message(self, chat_id, msg_id, **kw):
        if 'reply_markup' in kw.keys():
            kw['reply_markup'] = kw['reply_markup'].parse()

        msg_kw = {'chat_id': chat_id, 'message_id': msg_id, **kw}
        try:
            return Message(self.api('editMessageText', msg_kw))
        except APIError as e:
            if 'message is not modified' in e.args[0]:
                pass
            else:
                raise

    def forward_message(self, from_chat_id, chat_id, msg_id, disable_notification=False):
        """
        :param from_chat_id: Unique identifier for the chat where the original message was sent
        :param chat_id: Unique identifier for the target chat or username of the target channel
        :param msg_id: Message identifier in the chat specified in from_chat_id
        :param disable_notification: Optional. Sends the message silently. Users will receive a
                                     notification with no sound.
        :return: The forwarded message.
        """
        return Message(self.api('forwardMessage', {'from_chat_id': from_chat_id,
                                                   'chat_id': chat_id,
                                                   'message_id': msg_id,
                                                   'disable_notification': disable_notification}))

    def answer_callback_query(self, callback_query_id, **kwargs) -> bool:
        """
        :param callback_query_id: callback_query_id you receive in callback_query
        :param kwargs: Keyword arguments defined in Telegram bot api. You should always call this method after receiving
                       a valid callback_query, even if you have nothing to send back to user.
                       See https://core.telegram.org/bots/api#answercallbackquery
               - text: Optional. Text of the notification. If not specified, nothing will be shown to the
                       user, 0-200 characters.
               - show_alert: Optional. If true, an alert will be shown by the client instead of a notification
                             at the top of the chat screen. Defaults to false.
               - cache_time: Optional. The maximum amount of time in seconds that the result of the callback
                             query may be cached client-side. Telegram apps will support caching starting
                             in version 3.14. Defaults to 0.
        :return:
        """
        return self.api('answerCallbackQuery', {'callback_query_id': callback_query_id, **kwargs})

    def get_chat(self, chat_id: int):
        try:
            chat = Chat(self.api('getChat', {'chat_id': chat_id}))
        except APIError as e:
            if e.args[0] == 'Bad Request: chat not found':
                raise ChatNotFoundError
            else:
                raise
        else:
            return chat

    def get_chat_member(self, chat_id: int, user_id: int):
        """
        Typically, use this method to build a ChatMember object.
        :param chat_id: ID of the chat that the ChatMember object will belong to.
        :param user_id: ID of the target user.
        :return: A ChatMember object, including info about permissions granted to the user in a specific chat.
        """
        try:
            chat_member = ChatMember(self.api('getChatMember', {'chat_id': chat_id, 'user_id': user_id}), chat_id)
        except APIError as e:
            if 'Bad Request: user not found' in e.args[0]:
                raise UserNotFoundError
            else:
                raise
        else:
            return chat_member


class ChatMember(User):
    def __init__(self, member_json: dict, chat_id: int):
        """
        Typically, build a ChatMember object from Bot.get_chat_member() method, which automatically get corresponding
        Chat object.
        :param member_json: Raw response from "getChatMember" API
        :param chat_id: ID of the chat which this ChatMember belongs to.
        """
        super().__init__(member_json['user'])
        self.raw = f'{{"chat_member": {member_json}, "chat_id": {chat_id}}}'
        self.chat_id: int = chat_id
        # Can be “creator”, “administrator”, “member”, “restricted”, “left” or “kicked”
        self.status: str = member_json['status']
        if 'custom_title' in member_json.keys():
            self.custom_title: str = member_json['custom_title']
        if self.status == 'administrator':
            self.can_be_edited: bool = member_json['can_be_edited']
            self.can_delete_messages: bool = member_json['can_delete_messages']
            self.can_promote_members: bool = member_json['can_promote_members']
        if self.status == 'administrator' or self.status == 'restricted':
            self.can_change_info: bool = member_json['can_change_info']
            self.can_invite_users: bool = member_json['can_invite_users']
            self.can_pin_messages: bool = member_json['can_pin_messages']
        if self.status == 'restricted':
            self.is_member: bool = member_json['is_member']
            self.can_send_messages: bool = member_json['can_send_messages']
            self.can_send_media_messages: bool = member_json['can_send_media_messages']
            self.can_send_polls: bool = member_json['can_send_polls']
            self.can_send_other_messages: bool = member_json['can_send_other_messages']  # sticker, gif and inline bot
            self.can_add_web_page_previews: bool = member_json['can_add_web_page_previews']  # "embed links" in client

    def __str__(self):
        return self.raw


class Message:
    def __init__(self, msg_json: dict):
        self.raw = msg_json
        self.chat = Chat(msg_json['chat'])
        self.id: int = msg_json['message_id']
        if 'from' in msg_json.keys():
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
            if 'forward_signature' in msg_json.keys():
                self.forward_signature: str = msg_json['forward_signature']
            else:
                self.forward_signature = ''
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
        self.html_formatted_text = self.text
        if 'entities' in msg_json.keys() or 'caption_entities' in msg_json.keys():
            entity_type = 'entities' if 'entities' in msg_json.keys() else 'caption_entities'
            entity_to_be_formatted = []
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
                    entity_to_be_formatted.append(item)
                elif item['type'] == 'italic':
                    self.italics.append(self.text[offset:offset + length])
                    entity_to_be_formatted.append(item)
                elif item['type'] == 'underline':
                    self.underlines.append(self.text[offset:offset + length])
                    entity_to_be_formatted.append(item)
                elif item['type'] == 'strikethrough':
                    self.strikethroughs.append(self.text[offset:offset + length])
                    entity_to_be_formatted.append(item)
                elif item['type'] == 'code':
                    self.codes.append(self.text[offset:offset + length])
                    entity_to_be_formatted.append(item)
                elif item['type'] == 'text_link':
                    self.text_links.append((self.text[offset:offset + length], item['url']))
                    entity_to_be_formatted.append(item)
                elif item['type'] == 'text_mention':
                    self.text_mention.append((self.text[offset:offset + length], User(item['user'])))
                    entity_to_be_formatted.append(item)

            entity_to_be_formatted = sorted(entity_to_be_formatted, key=lambda x: x['offset'], reverse=True)
            for item in entity_to_be_formatted:
                offset = item['offset']
                length = item['length']
                if item['type'] == 'bold':
                    self.html_formatted_text = self.text[:offset] + f'<b>{self.text[offset:offset + length]}</b>' + \
                                               self.html_formatted_text[offset + length:]
                elif item['type'] == 'italic':
                    self.html_formatted_text = self.text[:offset] + f'<i>{self.text[offset:offset + length]}</i>' + \
                                               self.html_formatted_text[offset + length:]
                elif item['type'] == 'underline':
                    self.html_formatted_text = self.text[:offset] + f'<u>{self.text[offset:offset + length]}</u>' + \
                                               self.html_formatted_text[offset + length:]
                elif item['type'] == 'strikethrough':
                    self.html_formatted_text = self.text[:offset] + f'<s>{self.text[offset:offset + length]}</s>' + \
                                               self.html_formatted_text[offset + length:]
                elif item['type'] == 'code':
                    self.html_formatted_text = self.text[:offset] + \
                                               f'<code>{self.text[offset:offset + length]}</code>' +\
                                               self.html_formatted_text[offset + length:]
                elif item['type'] == 'text_link':
                    self.html_formatted_text = self.text[:offset] + f"<a href=\"{item['url']}\">" \
                                                                    f"{self.text[offset:offset + length]}</a>" + \
                                               self.html_formatted_text[offset + length:]
                elif item['type'] == 'text_mention':
                    self.html_formatted_text = self.text[:offset] + f"<a href=\"tg://user?id={item['user']['id']}\">" \
                                                                    f"{self.text[offset:offset + length]}</a>" + \
                                               self.html_formatted_text[offset + length:]

        if 'dice' in msg_json.keys():
            self.dice = True
            self.dice_emoji = msg_json['dice']['emoji']
            self.dice_value = msg_json['dice']['value']
        else:
            self.dice = False

        if 'reply_markup' in msg_json.keys():
            self.reply_markup: InlineKeyboard = InlineKeyboard.from_json(msg_json['reply_markup'])

    def __str__(self):
        return self.raw


class InlineKeyboardButton:
    def __init__(self, text: str, **kwargs):
        """
        :param text: Text showed on the button.
        :param kwargs: Other optional params defined in Telegram bot api.
                       See https://core.telegram.org/bots/api#inlinekeyboardbutton
            - url: Optional. HTTP or tg:// url to be opened when button is pressed
            - callback_data: Optional. Data to be sent in a callback query to the bot when button is pressed, 1-64 bytes
        """
        self.text = text
        if len(kwargs) == 0:
            raise APIError('Inline keyboard button must have either url or callback_data.')
        if 'url' in kwargs.keys():
            self.url = kwargs['url']
        if 'callback_data' in kwargs.keys():
            self.callback_data = kwargs['callback_data']

    @classmethod
    def from_json(cls, button_json: dict):
        return cls(**button_json)

    def parse(self) -> dict:
        """
        :return: self.__dict__ for follow up usage like json serialization.
        """
        return self.__dict__


class InlineKeyboard:
    def __init__(self, key_list: List[List[InlineKeyboardButton]]):
        """
        :param key_list: Use InlineKeyBoardButton to structure the buttons you want and pass it into this
                         initializer. Each sublist represent a row. Buttons in the same sublist will be
                         placed in the same row.
        """
        self.key_list = key_list

    @classmethod
    def from_json(cls, markup_json: dict):
        markup_list: List[List[dict]] = markup_json['inline_keyboard']
        key_list: List[List[InlineKeyboardButton]] = []
        for i in range(len(markup_json)):
            key_list.append([])
            for j in range(len(markup_json)):
                key_list[i].append(InlineKeyboardButton.from_json(markup_list[i][j]))

        return cls(key_list)

    def parse(self) -> Dict[str, List[List[Dict]]]:
        key_list: List[List[dict]] = []
        for i in range(len(self.key_list)):
            key_list.append([])
            for j in range(len(self.key_list[i])):
                key_list[i].append(self.key_list[i][j].parse())

        return {'inline_keyboard': key_list}


class CallbackQuery:
    def __init__(self, query_json: dict):
        self.raw = query_json
        self.id: str = query_json['id']
        self.from_ = User(query_json['from'])
        if 'message' not in query_json.keys():
            self.msg = ''
        else:
            self.msg = Message(query_json['message'])
        self.chat_instance: str = query_json['chat_instance']
        if 'data' in query_json.keys():
            self.data: str = query_json['data']
        else:
            self.data = ''
        if 'inline_message_id' in query_json.keys():
            self.inline_message_id: str = query_json['inline_message_id']
        else:
            self.inline_message_id = ''

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
        elif self.type != 'private' and str(self.id).startswith('-100'):
            self.username = ''
            self.link = f't.me/c/{str(self.id).replace("-100", "")}'
        else:
            self.username = ''
            self.link = ''

    def __str__(self):
        return self.raw


class APIError(Exception):
    pass


class UserNotFoundError(APIError):
    pass


class ChatNotFoundError(APIError):
    pass
