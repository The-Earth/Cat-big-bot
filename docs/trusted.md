# Trusted

trusted 用户是受信任的用户，可以执行一些易被滥用的指令。trusted 用户可由现有的 trusted 用户授权。

## 权限

* 可以使用所有用户均可使用的指令
* 于群组中可以使用：
    * [`/unmark`](mark.md)
    * `/set_trusted`
    * `/list_trusted`
* 于私聊中可以使用：
    * `/set_trusted`

## 权限管理指令

### /set_trusted

trusted 用户于群组或私聊中使用，将用户设置为 trusted 用户。使用方法：

回复需要标记为 trusted 的用户，内容为 `/set_trusted`

或

```
/set_trusted <用户ID> <用户ID> ...
```

### /list_trusted

trusted 用户于群组中使用，列出当前群组中的 trusted 用户。
