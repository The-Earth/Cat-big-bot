# mark

使用 mark 系列指令在群内建立公共备忘录。所有指令都需要在可以复制群消息链接（可以对某条消息使用 copy link）的群组使用，目前发现除了没有生成入群链接的私有群组，其余群组皆可复制消息链接。

## 指令

### /mark

在群组使用，标记指定消息。格式：

回复想要做标记的消息，内容为 `/mark <说明文字>`。说明文字可以为空。

### /list_marked

在群组使用，列出被标记的消息，同时附上相应的说明文字。

### /unmark

[`trusted`](trusted.md) 用户在群组使用，使消息不再被标记。使用方法：

回复需要取消标记的消息，内容为 `/unmark`

或

```
/unmark <消息ID> <消息ID> ...
```
