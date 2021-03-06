# Cat-big-bot
[多功能 Telegram 机器人](https://t.me/CatBigBot)

## 运行

机器人分为两部分，`responsive_tasks.py` 放置回应用户指令的功能，`sending_tasks.py` 放置根据其他信息源推送内容的功能（纯发送，不响应），目前只有中文维基百科新页面推送。运行机器人时直接运行这两个文件。

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
