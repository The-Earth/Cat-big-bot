# Admin

admin 用户由机器人操作者授权，是可以管理较高级功能的用户（和 Telegram 群组的 admin 无关）。

## 可管理的功能

* [投票](poll.md)
* [频道讨论群辅助](channel_helper.md)

## 权限列表
* 可以使用 [trusted](trusted.md) 用户可使用的指令
* 可以使用 [voter](voter.md) 用户可使用的指令
* 于群组中可以使用：
    * [`/set_voter`](voter.md)
    * [`/list_voter`](voter.md)
    * [`/unset_voter`](voter.md)
    * [`/init_poll`](poll.md)
    * [点按开始投票按钮](poll.md)
    * [点按取消投票按钮](poll.md)
    * [点按关闭投票按钮](poll.md)
    * [`/set_channel_helper`](channel_helper.md)
    * [`/unset_channel_helper`](channel_helper.md)

## 权限管理指令

### /set_admin

机器人操作者于群组或私聊中使用，将用户设置为管理员。使用方法：

回复需要授予 admin 的用户，内容为 `/set_admin`

或

```
/set_admin <用户ID> <用户ID> ...
```
