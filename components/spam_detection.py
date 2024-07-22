from io import BytesIO

import catbot
import torch
import torch.nn as nn
from torchvision import transforms
from PIL import Image
from telethon import TelegramClient, events
from telethon.events.newmessage import NewMessage

from components import bot

__all__ = [
    'porn_detect_tester',
    'porn_detect_main'
]


class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()

        self.conv1 = nn.Conv2d(3, 16, 3, padding='same')
        self.conv2_1 = nn.Conv2d(16, 16, 3, padding='same')
        self.conv2_2 = nn.Conv2d(16, 16, 3, padding='same')
        self.conv2_3 = nn.Conv2d(16, 16, 3, padding='same')
        self.conv2_4 = nn.Conv2d(16, 16, 3, padding='same')

        self.conv3 = nn.Conv2d(16, 32, 3, padding='same')
        self.conv3_1 = nn.Conv2d(32, 32, 3, padding='same')
        self.conv3_res = nn.Conv2d(16, 32, 1, stride=2)
        self.conv3_2 = nn.Conv2d(32, 32, 3, padding='same')
        self.conv3_3 = nn.Conv2d(32, 32, 3, padding='same')

        self.conv4 = nn.Conv2d(32, 64, 3, padding='same')
        self.conv4_1 = nn.Conv2d(64, 64, 3, padding='same')
        self.conv4_res = nn.Conv2d(32, 64, 1, stride=2)
        self.conv4_2 = nn.Conv2d(64, 64, 3, padding='same')
        self.conv4_3 = nn.Conv2d(64, 64, 3, padding='same')

        self.conv5 = nn.Conv2d(64, 128, 3, padding='same')
        self.conv5_1 = nn.Conv2d(128, 128, 3, padding='same')
        self.conv5_res = nn.Conv2d(64, 128, 1, stride=2)
        self.conv5_2 = nn.Conv2d(128, 128, 3, padding='same')
        self.conv5_3 = nn.Conv2d(128, 128, 3, padding='same')

        self.conv6 = nn.Conv2d(128, 256, 3, padding='same')
        self.conv6_1 = nn.Conv2d(256, 256, 3, padding='same')
        self.conv6_res = nn.Conv2d(128, 256, 1, stride=2)
        self.conv6_2 = nn.Conv2d(256, 256, 3, padding='same')
        self.conv6_3 = nn.Conv2d(256, 256, 3, padding='same')

        self.max_pool = nn.MaxPool2d(2)
        self.avg_pool = nn.AvgPool2d(2)

        self.fc1 = nn.Linear(4096, 1024)
        self.fc2 = nn.Linear(1024, 128)
        self.fc3 = nn.Linear(128, 16)
        self.fc4 = nn.Linear(16, 1)

    def forward(self, x):
        x1 = self.max_pool(torch.relu(self.conv1(x)))
        x2 = torch.relu(self.conv2_1(x1))
        x2 = torch.relu(self.conv2_2(x2))
        x1 = torch.relu(x1 + x2)
        x2 = torch.relu(self.conv2_3(x1))
        x2 = torch.relu(self.conv2_4(x2))
        x1 = torch.relu(x1 + x2)

        x2 = self.max_pool(torch.relu(self.conv3(x1)))
        x2 = torch.relu(self.conv3_1(x2))
        x3 = torch.relu(self.conv3_res(x1))
        x1 = torch.relu(x2 + x3)
        x2 = torch.relu(self.conv3_2(x1))
        x2 = torch.relu(self.conv3_3(x2))
        x1 = torch.relu(x1 + x2)

        x2 = self.max_pool(torch.relu(self.conv4(x1)))
        x2 = torch.relu(self.conv4_1(x2))
        x3 = torch.relu(self.conv4_res(x1))
        x1 = torch.relu(x2 + x3)
        x2 = torch.relu(self.conv4_2(x1))
        x2 = torch.relu(self.conv4_3(x2))
        x1 = torch.relu(x1 + x2)

        x2 = self.max_pool(torch.relu(self.conv5(x1)))
        x2 = torch.relu(self.conv5_1(x2))
        x3 = torch.relu(self.conv5_res(x1))
        x1 = torch.relu(x2 + x3)
        x2 = torch.relu(self.conv5_2(x1))
        x2 = torch.relu(self.conv5_3(x2))
        x1 = torch.relu(x1 + x2)

        x2 = self.max_pool(torch.relu(self.conv6(x1)))
        x2 = torch.relu(self.conv6_1(x2))
        x3 = torch.relu(self.conv6_res(x1))
        x1 = torch.relu(x2 + x3)
        x2 = torch.relu(self.conv6_2(x1))
        x2 = torch.relu(self.conv6_3(x2))
        x1 = torch.relu(x1 + x2)

        x1 = self.avg_pool(x1)

        x = torch.flatten(x1, start_dim=1)

        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        x = torch.relu(self.fc3(x))
        x = torch.sigmoid(self.fc4(x))
        return x


def pred_score(image: Image) -> float:
    transformer = transforms.Compose([
        transforms.PILToTensor(),
        transforms.ConvertImageDtype(torch.float32),
    ])
    image_tensor = transformer(image)

    h_start = torch.randint(0, image_tensor.shape[1] - 256, (1,)) if image_tensor.shape[1] > 256 else 0
    w_start = torch.randint(0, image_tensor.shape[2] - 256, (1,)) if image_tensor.shape[2] > 256 else 0
    image_tensor = image_tensor[:, h_start: h_start + 256, w_start: w_start + 256][None, :]

    net = Net()
    net.load_state_dict(torch.load(bot.config['porn_detection_model'], map_location='cpu'))
    with torch.no_grad():
        pred = net(image_tensor)
    return pred.item()


def porn_detect_tester_cri(msg: catbot.Message) -> bool:
    return msg.chat.id == bot.config['operator_id'] and msg.has_photo


@bot.msg_task(porn_detect_tester_cri)
def porn_detect_tester(msg: catbot.Message):
    if not msg.has_photo:
        return
    photo = msg.photo[-1]
    file = bot.get_file(photo.file_id)
    image = Image.open(BytesIO(bot.download(file)))
    pred = pred_score(image)
    prob = f'{pred * 100:.2f}'

    bot.send_message(msg.chat.id, text=bot.config['messages']['porn_detection_tester'].format(prob=prob),
                     reply_to_message_id=msg.id)


def porn_detect_main():
    client = TelegramClient('spam_detection', bot.config['api_id'], bot.config['api_hash'])

    @client.on(events.NewMessage())
    async def porn_detect(event: NewMessage):
        chat_id = event.chat_id
        if chat_id in bot.config['porn_exempt_chat']:
            return
        sender = event.from_id
        if hasattr(sender, 'user_id'):
            _ = sender.user_id
        else:
            return
        if event.photo is None:
            return
        # if int(chat_id) == bot.id or int(user_id) < 5400000000:   # TODO
        #     return
        msg_id = event.id

        photo_buff = await event.download_media(file=bytes, thumb=-1)
        image = Image.open(BytesIO(photo_buff))
        if image.size[0] < 256 or image.size[1] < 256:
            return
        bot.api('sendChatAction', {'chat_id': bot.config['porn_alert_chat'], 'action': 'typing'})
        pred = pred_score(image)
        if pred > 0.8:  # TODO
            link = f't.me/c/{str(chat_id).replace("-100", "")}/{msg_id}'
            prob_text = f'{pred * 100:.0f}%'
            bot.send_message(
                bot.config['porn_alert_chat'],
                text=bot.config['messages']['porn_detected_alert'].format(link=link, prob=prob_text)
            )

    client.start()
    client.run_until_disconnected()
