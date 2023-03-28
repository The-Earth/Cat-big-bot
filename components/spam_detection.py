from io import BytesIO

import catbot
import torch
import torch.nn as nn
from torchvision import transforms
from PIL import Image
from telethon import TelegramClient, events
from telethon.events.newmessage import NewMessage

from components import bot, config


class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()

        self.conv1 = nn.Conv2d(3, 6, 3, padding='same')
        self.conv2_1 = nn.Conv2d(6, 6, 3, padding='same')
        self.conv2_2 = nn.Conv2d(6, 6, 3, padding='same')
        self.conv2_3 = nn.Conv2d(6, 6, 3, padding='same')
        self.conv2_4 = nn.Conv2d(6, 6, 3, padding='same')

        self.conv3 = nn.Conv2d(6, 12, 3, padding='same')
        self.conv3_1 = nn.Conv2d(12, 12, 3, padding='same')
        self.conv3_res = nn.Conv2d(6, 12, 1, stride=2)
        self.conv3_2 = nn.Conv2d(12, 12, 3, padding='same')
        self.conv3_3 = nn.Conv2d(12, 12, 3, padding='same')

        self.conv4 = nn.Conv2d(12, 24, 3, padding='same')
        self.conv4_1 = nn.Conv2d(24, 24, 3, padding='same')
        self.conv4_res = nn.Conv2d(12, 24, 1, stride=2)
        self.conv4_2 = nn.Conv2d(24, 24, 3, padding='same')
        self.conv4_3 = nn.Conv2d(24, 24, 3, padding='same')

        self.max_pool = nn.MaxPool2d(2)
        self.avg_pool = nn.AvgPool2d(2)

        self.fc1 = nn.Linear(1536, 256)
        self.fc2 = nn.Linear(256, 64)
        self.fc3 = nn.Linear(64, 16)

        self.fc4 = nn.Linear(400, 80)
        self.fc5 = nn.Linear(80, 10)
        self.fc6 = nn.Linear(10, 1)

    def forward(self, x):
        sub_tensors = [x[:, :, i * 128:((i + 1) * 128)] for i in range(25)]
        sub_output = []

        for i, item in enumerate(sub_tensors):
            x1 = self.max_pool(torch.relu(self.conv1(item)))
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

            x1 = self.avg_pool(x1)

            x1 = torch.flatten(x1, start_dim=1)

            x1 = torch.relu(self.fc1(x1))
            x1 = torch.relu(self.fc2(x1))
            x1 = torch.relu(self.fc3(x1))

            sub_output.append(torch.flatten(x1, start_dim=1))

        x = torch.cat(sub_output, dim=1)
        x = torch.relu(self.fc4(x))
        x = torch.relu(self.fc5(x))
        x = torch.sigmoid(self.fc6(x))

        return x


def pred_score(image: Image) -> float:
    if image.size[0] < 128 or image.size[1] < 128:
        return 0.
    transformer = transforms.Compose([
        transforms.PILToTensor(),
        transforms.ConvertImageDtype(torch.float32),
    ])
    image_tensor = transformer(image)

    sub_images = []
    for i in range(25):
        h_start = torch.randint(0, image_tensor.shape[1] - 128, (1,))
        w_start = torch.randint(0, image_tensor.shape[2] - 128, (1,))
        sub_images.append(image_tensor[:, h_start:h_start + 128, w_start:w_start + 128])
    sub_tensors = torch.cat(sub_images, dim=1)[None, :]

    net = Net()
    net.load_state_dict(torch.load(config['porn_detection_model'], map_location='cpu'))
    with torch.no_grad():
        pred = net(sub_tensors)
    return pred.item()


def porn_detect_tester_cri(msg: catbot.Message) -> bool:
    return msg.chat.id == config['operator_id'] and msg.has_photo


def porn_detect_tester(msg: catbot.Message):
    if not msg.has_photo:
        return
    photo = msg.photo[-1]
    file = bot.get_file(photo.file_id)
    image = Image.open(BytesIO(bot.download(file)))
    pred = pred_score(image)
    prob = f'{pred * 100:.2f}'

    bot.send_message(msg.chat.id, text=config['messages']['porn_detection_tester'].format(prob=prob),
                     reply_to_message_id=msg.id)


def porn_detect_main():
    client = TelegramClient('detect', config['api_id'], config['api_hash'])

    @client.on(events.NewMessage())
    async def porn_detect(event: NewMessage):
        chat_id = event.chat_id
        sender = event.from_id
        if hasattr(sender, 'user_id'):
            user_id = sender.user_id
        else:
            return
        if event.photo is None:
            return
        if int(chat_id) == bot.id or int(user_id) < 5400000000:
            return
        msg_id = event.id

        photo_buff = await event.download_media(file=bytes, thumb=-1)
        image = Image.open(BytesIO(photo_buff))
        if image.size[0] < 200 or image.size[1] < 200:
            return
        bot.api('sendChatAction', {'chat_id': config['porn_alert_chat'], 'action': 'typing'})
        pred = pred_score(image)
        if pred > 0.7:
            link = f't.me/c/{str(chat_id).replace("-100", "")}/{msg_id}'
            prob_text = f'{pred * 100:.0f}%'
            bot.send_message(config['porn_alert_chat'],
                             text=config['messages']['porn_detected_alert'].format(link=link, prob=prob_text))

    client.start()
    client.run_until_disconnected()
