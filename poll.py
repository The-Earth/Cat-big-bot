from typing import List
import time


class Poll:
    def __init__(self, chat_id: int, id_: int):
        self.title = ''
        self.option_list: List[dict] = []
        self.open = False
        self.start_time = 0
        self.last_time = 0
        self.readable_time = ''
        # if anonymous when the poll is open
        self.anonymous_open = False
        # if anonymous when the poll is closed
        self.anonymous_closed = False
        # if count of each option is available when the poll is open
        self.count_open = False
        # if the poll allows multiple choices
        self.multiple = False
        self.id_ = id_
        self.chat_id = chat_id

    def start(self):
        if self.open:
            return
        self.start_time = time.time()
        self.open = True

    def stop(self):
        if not self.open:
            return
        self.open = False

    def set_option(self, op_list: List[str]):
        if self.open:
            return
        for i in range(len(op_list)):
            self.option_list.append({'text': op_list[i], 'user': []})

    def vote(self, user_id: int, option_id: int):
        if not self.open:
            return

        if not self.multiple:
            for i in range(len(self.option_list)):
                if i == option_id:
                    continue
                if user_id in self.option_list[i]['user']:
                    self.option_list[i]['user'].remove(user_id)

        if user_id in self.option_list[option_id]['user']:
            self.option_list[option_id]['user'].remove(user_id)
        else:
            self.option_list[option_id]['user'].append(user_id)

    def to_json(self):
        return self.__dict__

    @classmethod
    def from_json(cls, data: dict):
        obj = cls(data['chat_id'], data['id_'])
        obj.title = data['title']
        obj.option_list = data['option_list']
        obj.open = data['open']
        obj.start_time = data['start_time']
        obj.last_time = data['last_time']
        obj.anonymous_open = data['anonymous_open']
        obj.anonymous_closed = data['anonymous_closed']
        obj.count_open = data['count_open']
        obj.multiple = data['multiple']

        return obj
