# 私聊

用户可通过机器人与操作者私聊。

## 指令

### /pass

私聊使用，格式：

```
/pass <消息内容>
```

主人会通过机器人收到命令使用者发来的消息。暂时仅支持纯文字。

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