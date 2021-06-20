# channel helper

为了给频道的每条推送文章添加讨论区，可以为其绑定相应的群组。若要阻止用户在群组中发言，而非从频道中进入发言区，可启用本功能。

## 指令

### /set_channel_helper

[trusted 用户](trusted.md)在群组中使用，启用本功能。同时需授予 `ban user` 和 `delete message` 权限来完成踢人和删除入群消息的操作。机器人会自动将自己主动入群者踢出群组，然后解封。于是用户不能入群，但仍可以在频道讨论区中发言。

### /unset_channel_helper

[trusted 用户](trusted.md)在群组中使用，关闭本功能。
