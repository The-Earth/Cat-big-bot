import asyncio
from io import BytesIO

import catbot
import torch
import torch.nn as nn
from torchvision.transforms import PILToTensor
from PIL import Image
from telethon import TelegramClient, events
from telethon.tl.types import Photo
from telethon.events.newmessage import NewMessage

from components import bot, config


class Net(nn.Module):
    def __init__(self):
        """
        Input: (180, 320)
        """
        super(Net, self).__init__()

        self.conv1 = nn.Conv2d(3, 6, 3)
        self.conv2 = nn.Conv2d(6, 12, 3)
        self.conv3 = nn.Conv2d(12, 18, 3)
        self.conv4 = nn.Conv2d(18, 24, 5)

        self.conv5 = nn.Conv2d(3, 6, 11)
        self.conv6 = nn.Conv2d(6, 12, 9)
        self.conv7 = nn.Conv2d(12, 18, 9)
        self.conv8 = nn.Conv2d(18, 24, 9)

        self.pool = nn.MaxPool2d(2)

        self.fc1 = nn.Linear(4128, 1024)
        self.fc2 = nn.Linear(1024, 128)
        self.fc3 = nn.Linear(128, 16)
        self.fc4 = nn.Linear(16, 1)

    def forward(self, x):
        x1 = torch.relu(self.pool(self.conv1(x)))
        x1 = torch.relu(self.pool(self.conv2(x1)))
        x1 = torch.relu(self.pool(self.conv3(x1)))
        x1 = torch.relu(self.pool(self.conv4(x1)))
        x1 = torch.flatten(x1, start_dim=1)

        x2 = torch.relu(self.pool(self.conv5(x)))
        x2 = torch.relu(self.pool(self.conv6(x2)))
        x2 = torch.relu(self.pool(self.conv7(x2)))
        x2 = torch.relu(self.pool(self.conv8(x2)))
        x2 = torch.flatten(x2, start_dim=1)

        x = torch.cat((x1, x2), 1)

        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        x = torch.relu(self.fc3(x))
        x = torch.sigmoid(self.fc4(x))

        return x


def porn_detect_tester_cri(msg: catbot.Message) -> bool:
    return msg.chat.id == config['operator_id'] and msg.has_photo


def porn_detect_tester(msg: catbot.Message):
    if not msg.has_photo:
        return
    photo = msg.photo[-1]
    file = bot.get_file(photo.file_id)
    image = Image.open(BytesIO(bot.download(file)))
    if image.size[0] > image.size[1]:
        image = image.rotate(90)
    image = image.resize((180, 320))
    transformer = PILToTensor()
    image_tensor = (transformer(image).float() / 255.)[None, :]

    net = Net()
    net.load_state_dict(torch.load(config['porn_detection_model'], map_location='cpu'))
    with torch.no_grad():
        pred = net(image_tensor)
    prob = f'{pred.item() * 100:.2f}'

    bot.send_message(msg.chat.id, text=config['messages']['porn_detection_tester'].format(prob=prob),
                     reply_to_message_id=msg.id)


def porn_detect_main():
    client = TelegramClient('detect', config['api_id'], config['api_hash'])

    @client.on(events.NewMessage())
    async def porn_detect(event: NewMessage):
        chat_id = event.chat_id
        msg_id = event.id
        photo: Photo = event.photo

        if photo is not None:
            photo_buff = await event.download_media(file=bytes, thumb=-1)
            image = Image.open(BytesIO(photo_buff))
            if image.size[0] > image.size[1]:
                image = image.rotate(90)
            image = image.resize((180, 320))
            transformer = PILToTensor()
            image_tensor = (transformer(image).float() / 255.)[None, :]

            net = Net()
            net.load_state_dict(torch.load(config['porn_detection_model'], map_location='cpu'))
            with torch.no_grad():
                pred = net(image_tensor)
            if pred > 0.8:
                link = f't.me/c/{str(chat_id).replace("-100", "")}/{msg_id}'
                prob_text = f'{pred.item() * 100:.0f}%'
                bot.send_message(config['porn_alert_chat'],
                                 text=config['messages']['porn_detected_alert'].format(link=link, prob=prob_text))

    client.start()
    client.run_until_disconnected()
