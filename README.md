# Cat-big-bot
t.me/CatBigBot

## 用户权限
* 所有用户
    * 于群组中可以使用：
        * `/chat_id`
        * `/user_id`
        * `/mark`
        * `/list_marked`
        * `/start_new_pages`
        * `/set_ns`
        * `/list_ns`
        * `/stop_new_pages`
    * 于私聊中可以使用：
        * `/start`
        * `/chat_id`
        * `/user_id`
        * `/start_new_pages`
        * `/set_ns`
        * `/list_ns`
        * `/stop_new_pages`
        * `/help`
        * `/pass`
        * `/permalink`
* trusted 用户
    * 可以使用所有用户均可使用的指令
    * 于群组中可以使用：
        * `/unmark`
        * `/help@CatBigBot` (必须含有 `@CatBigBot`)
        * `/set_trusted`
        * `/list_trusted`
    * 于私聊中可以使用：
        * `/set_trusted`
* blocked 用户
    * 可以使用所有用户均可使用的指令，但
    * 无法使用：
        * `/pass`
* admin 用户
    * （即将出现）
* voter 用户
    * （即将出现）
* operator （机器人操作者）
    * 可以使用所有用户均可使用的指令”
    * 可以使用 trusted 用户可使用的指令
    * 于私聊中可以使用：
        * `/reply`
        * `/block`
        * `/unblock`
        * `/list_blocked`

## 指令

### /user_id

查看他人或自己的 ID，使用方法：

* 查看自己的 ID：直接发送 `/user_id`
* 查看他人的 ID：回复想被获取ID者发出的消息，内容为 `/user_id`

### /chat_id

查看当前聊天的 ID。当前聊天可以是:

* 群组（得到群组 ID）
* 私聊（得到自己的用户 ID）

### /pass

私聊使用，格式：

```
/pass <消息内容>
```

主人会通过机器人收到命令使用者发来的消息。

### /reply
操作者私聊使用，格式：

```
/reply <用户ID> <消息内容>
```

指定 ID 的用户会收到主人的回复。

### /block

操作者私聊使用，格式：

```
/block <用户ID> <用户ID> ...
```

禁止指定 ID 的用户通过 `/pass` 发送消息，可以指定多个 ID。

### /unblock

操作者私聊使用，格式：

```
/unblock <用户ID> <用户ID> ...
```

不再禁止指定 ID 的用户通过 `/pass` 发送消息，可以指定多个 ID。

### /list_blocked

操作者私聊使用，列出被禁止通过 `/pass` 发送消息的用户。

### /mark

在群内消息可以复制链接（copy link）的群组使用，标记指定消息。使用方法：回复想要做标记的消息，内容为 `/mark`

### /list_marked

在群内消息可以复制链接（copy link）的群组使用，列出被标记的消息。

### /unmark

在群内消息可以复制链接（copy link）的群组使用，使消息不再被标记。使用方法：

回复需要取消标记的消息，内容为 `/unmark`

或

```
/unmark <消息ID> <消息ID> ...
```

### /set_trusted

将用户设置为 trusted 用户。使用方法：

回复需要标记为 trusted 的用户，内容为 `/set_trusted`

或

```
/set_trusted <用户ID> <用户ID> ...
```

### /list_trusted

在群组中使用，列出当前群组中的 trusted 用户。

### /permalink

在私聊中使用，尝试获得指向指定 ID 用户的链接。此链接不受 username 变化影响。格式：

```
/permalink <用户ID>
```

### /start_new_pages

在当前对话（私聊或群组）中开启中文维基百科新页面推送，需设置所要推送的名字空间（见下）。

### /set_ns

设置中文维基百科新页面推送的名字空间，以编号指定名字空间（见下）。可以在开启或关闭推送的状态下使用。格式：

```
/set_ns <ns1> <ns2> ...
```

例：推送全部名字空间：

```
/set_ns -1
```

例：推送条目和草稿：

```
/set_ns 0 118
```

### /list_ns

显示中文维基百科名字空间和编号对应表。（不知道名字空间是什么？那您还是别用这个功能了）

### /stop_new_pages

在当前对话（私聊或群组）中关闭中文维基百科新页面推送。
