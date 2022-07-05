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
        Input: (1600, 64)
        """
        super(Net, self).__init__()

        self.conv1 = nn.Conv2d(3, 6, 3)
        self.conv2 = nn.Conv2d(6, 12, 3)
        self.conv3 = nn.Conv2d(12, 18, 3)
        self.conv4 = nn.Conv2d(18, 24, 3)

        self.pool = nn.MaxPool2d(2)

        self.fc1 = nn.Linear(9600, 2048)
        self.fc2 = nn.Linear(2048, 512)
        self.fc3 = nn.Linear(512, 128)
        self.fc4 = nn.Linear(128, 16)
        self.fc5 = nn.Linear(16, 1)

    def forward(self, x):
        sub_tensors = [x[:, :, i * 64:((i + 1) * 64)] for i in range(25)]
        sub_output = []

        for i, item in enumerate(sub_tensors):
            x1 = torch.relu(self.pool(self.conv1(item)))
            x1 = torch.relu(self.pool(self.conv2(x1)))
            x1 = torch.relu(self.pool(self.conv3(x1)))
            x1 = torch.relu(self.conv4(x1))
            sub_output.append(torch.flatten(x1, start_dim=1))

        x = torch.cat(sub_output, dim=1)
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        x = torch.relu(self.fc3(x))
        x = torch.relu(self.fc4(x))
        x = torch.sigmoid(self.fc5(x))

        return x


def porn_detect_tester_cri(msg: catbot.Message) -> bool:
    return msg.chat.id == config['operator_id'] and msg.has_photo


def porn_detect_tester(msg: catbot.Message):
    if not msg.has_photo:
        return
    photo = msg.photo[-1]
    file = bot.get_file(photo.file_id)
    image = Image.open(BytesIO(bot.download(file)))
    transformer = PILToTensor()
    image_tensor = (transformer(image).float() / 255.)[None, :]

    if image.size[0] < 64 or image.size[1] < 64:
        return

    transformer = PILToTensor()
    image_tensor = (transformer(image).float() / 255.)

    sub_images = []
    h_num = min(image_tensor.shape[1] // 64, 5)
    w_num = min(image_tensor.shape[2] // 64, 5)
    for i in range(5):
        for j in range(5):
            if i < h_num < 5:
                h_start = (h_num - 1) * 64
            elif h_num < 5 and i >= h_num:
                h_start = h_num - 1
            else:
                h_start = i * (image_tensor.shape[1] // 5)
            if j < w_num < 5:
                w_start = (w_num - 1) * 64
            elif w_num < 5 and i >= w_num:
                w_start = w_num - 1
            else:
                w_start = i * (image_tensor.shape[2] // 5)
            sub_images.append(image_tensor[:, h_start:h_start + 64, w_start:w_start + 64])
    sub_tensors = torch.cat(sub_images, dim=1)[None, :]

    net = Net()
    net.load_state_dict(torch.load(config['porn_detection_model'], map_location='cpu'))
    with torch.no_grad():
        pred = net(sub_tensors)
    prob = f'{pred.item() * 100:.2f}'

    bot.send_message(msg.chat.id, text=config['messages']['porn_detection_tester'].format(prob=prob),
                     reply_to_message_id=msg.id)


def porn_detect_main():
    client = TelegramClient('detect', config['api_id'], config['api_hash'])

    @client.on(events.NewMessage())
    async def porn_detect(event: NewMessage):
        chat_id = event.chat_id
        if int(chat_id) == config['operator_id']:
            return
        msg_id = event.id
        photo: Photo = event.photo

        if photo is not None:
            photo_buff = await event.download_media(file=bytes, thumb=-1)
            image = Image.open(BytesIO(photo_buff))

            if image.size[0] < 64 or image.size[1] < 64:
                return

            transformer = PILToTensor()
            image_tensor = (transformer(image).float() / 255.)

            sub_images = []
            h_num = min(image_tensor.shape[1] // 64, 5)
            w_num = min(image_tensor.shape[2] // 64, 5)
            for i in range(5):
                for j in range(5):
                    if i < h_num < 5:
                        h_start = (h_num - 1) * 64
                    elif h_num < 5 and i >= h_num:
                        h_start = h_num - 1
                    else:
                        h_start = i * (image_tensor.shape[1] // 5)
                    if j < w_num < 5:
                        w_start = (w_num - 1) * 64
                    elif w_num < 5 and i >= w_num:
                        w_start = w_num - 1
                    else:
                        w_start = i * (image_tensor.shape[2] // 5)
                    sub_images.append(image_tensor[:, h_start:h_start + 64, w_start:w_start + 64])
            sub_tensors = torch.cat(sub_images, dim=1)[None, :]

            net = Net()
            net.load_state_dict(torch.load(config['porn_detection_model'], map_location='cpu'))
            with torch.no_grad():
                pred = net(sub_tensors)
            if pred > 0.5:
                link = f't.me/c/{str(chat_id).replace("-100", "")}/{msg_id}'
                prob_text = f'{pred.item() * 100:.0f}%'
                bot.send_message(config['porn_alert_chat'],
                                 text=config['messages']['porn_detected_alert'].format(link=link, prob=prob_text))

    client.start()
    client.run_until_disconnected()
