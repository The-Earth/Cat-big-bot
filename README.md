# Cat-big-bot
[多功能 Telegram 机器人](https://t.me/CatBigBot)

## 运行

```bash
python3 main.py
```

机器人依赖于 [catbot](https://github.com/The-Earth/catbot) 框架。

`config_example.json` 是配置文件示例，将 `token`、`operator_id` 等配置修改好之后，把文件保存至 `config.json` 即可使用。

## 用户权限

* [用户权限](docs/user_right.md)

## 投票

* [使用投票](docs/poll.md)
* [voter 用户](docs/voter.md)

## trusted 用户

* [trusted 用户](docs/trusted.md)

## 群组备忘录

* [mark 指令](docs/mark.md)

## 与操作者对话

* [私聊指令](docs/pm.md)

## 中文维基百科新页面推送

* [新页面推送](docs/new_pages.md)

## 其他指令

### /user_id

查看他人或自己的 ID，使用方法：

* 查看自己的 ID：直接发送 `/user_id`
* 查看他人的 ID：回复被获取ID者发出的消息，内容为 `/user_id`

### /chat_id

查看当前聊天的 ID。当前聊天可以是:

* 群组（得到群组 ID）
* 私聊（得到自己的用户 ID）

### /permalink

在私聊中使用，尝试获得指向指定 ID 用户的链接。此链接不受 username 变化影响。格式：

```
/permalink <用户ID>
```

### /help

在群组中或私聊中使用，显示帮助链接。在群组中使用时必须含有 `@CatBigBot` （或您机器人的 username）后缀。

### 垃圾图片检测

此功能使用预先训练好的模型检测聊天中出现的图片，对可能的垃圾图片在设定好的`chat_id`中报告。作为临时解决方案，使用[Telethon](https://github.com/LonamiWebs/Telethon)登入人类账号来获取图片。模型训练使用[Spam-Image-Detection](https://github.com/The-Earth/Spam-Image-Detection)项目。没有设计指令开关。
