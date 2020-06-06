import requests


class User:
    def __init__(self, user_json: dict):
        self.id: int = user_json['id']
        self.is_bot: bool = user_json['is_bot']
        if 'last_name' in user_json:
            self.name = f"{user_json['first_name']} {user_json['last_name']}"
        else:
            self.name = user_json['first_name']
        if 'username' in user_json:
            self.username = user_json['username']
        else:
            self.username = ''


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
            raise UpdateError('Bot initialization failed.' + get_me_resp['description'])

        super().__init__(get_me_resp['result'])

        self.can_join_groups: bool = get_me_resp['result']['can_join_groups']
        self.can_read_all_group_messages: bool = get_me_resp['result']['can_read_all_group_messages']
        self.supports_inline_queries: bool = get_me_resp['result']['supports_inline_queries']

        self.tasks = []

    def get_updates(self, offset: int, timeout: int = 60) -> list:
        post_data = {'offset': offset,
                     'timeout': timeout}
        update_resp: dict = requests.post(self.base_url + 'getUpdates', data=post_data, **self.proxy_kw).json()

        if not update_resp['ok']:
            raise UpdateError('Update getting failed.' + update_resp['description'])

        return update_resp['result']

    def add_task(self, criteria, action, **action_kw):
        """
        :param criteria:
            A function that lead flow of program into "action" function. It should take a Message object as the only
            argument and returns a bool. When it returns True, "action" will be executed. An example is to return
            True if the message starts with "/start", which is the standard starting of private chats with users.
        :param action:
            A function to be executed when criteria returns True. Typically it's the response on users' actions.
            It should take a Message object as the only positional argument and accept keyword arguments. Arguments in
            action_kw will be passed to it.
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
                update_offset = item['id'] + 1
                if 'message' in item.keys():
                    msg = Message(item['message'])
                elif 'edited_message' in item.keys():
                    msg = Message(item['edited_message'])
                else:
                    continue

                for criteria, action, action_kw in self.tasks:
                    if criteria(Message):
                        action(msg, **action_kw)


class Message:
    def __init__(self, msg_json: dict):
        self.chat = Chat(msg_json['chat'])
        self.id = msg_json['message_id']


class Chat:
    def __init__(self, chat_json: dict):
        pass


class UpdateError(Exception):
    pass
