# 用户权限

用户权限仅控制用户所能使用的本机器人的指令，且与群组无关。一名用户若属于某个用户组，则可以在任何群组使用相应指令，除非另有说明。

* 所有用户
    * 于群组中可以使用：
        * [`/chat_id`](../README.md '其他指令')
        * [`/user_id`](../README.md '其他指令')
        * [`/mark`](mark.md)
        * [`/list_marked`](mark.md)
        * [`/start_new_pages`](new_pages.md)
        * [`/set_ns`](new_pages.md)
        * [`/list_ns`](new_pages.md)
        * [`/stop_new_pages`](new_pages.md)
        * `/help@CatBigBot` （必须含有 `@CatBigBot` 或您机器人的 username）
    * 于私聊中可以使用：
        * `/start`
        * [`/chat_id`](../README.md '其他指令')
        * [`/user_id`](../README.md '其他指令')
        * [`/start_new_pages`](new_pages.md)
        * [`/set_ns`](new_pages.md)
        * [`/list_ns`](new_pages.md)
        * [`/stop_new_pages`](new_pages.md)
        * `/help`
        * [`/pass`](pm.md)
        * [`/permalink`](../README.md '其他指令')
* [trusted](trusted.md) 用户
    * 可以使用所有用户均可使用的指令
    * 于群组中可以使用：
        * [`/unmark`](mark.md)
        * [`/set_trusted`](trusted.md)
        * [`/list_trusted`](trusted.md)
    * 于私聊中可以使用：
        * [`/set_trusted`](trusted.md)
* [blocked 用户](pm.md)
    * 可以使用所有用户均可使用的指令，但
    * 无法使用：
        * [`/pass`](pm.md)
* [admin](admin.md) 用户
    * 可以使用 trusted 用户可使用的指令
    * 可以使用 voter 用户可使用的指令
    * 于群组中可以使用：
        * [`/set_voter`](voter.md)
        * [`/list_voter`](voter.md)
        * [`/unset_voter`](voter.md)
        * [`/init_poll`](poll.md)
        * [`/start_poll`](poll.md)
        * [点按开始投票按钮](poll.md)
        * [点按结束投票按钮](poll.md)
    * 于私聊中可以使用：
        * [`/set_voter`](voter.md)
        * [`/unset_voter`](voter.md)
* [voter](voter.md) 用户
    * 于群组中可以使用：
        * [点按投票选项](poll.md)
* operator （机器人操作者）
    * 可以使用所有用户均可使用的指令
    * 可以使用 trusted 用户可使用的指令
    * 可以使用 admin 用户可使用的指令
    * 于群组中可以使用：
        * [`/set_admin`](admin.md)
    * 于私聊中可以使用：
        * [`/reply`](pm.md)
        * [`/block`](pm.md)
        * [`/unblock`](pm.md)
        * [`/list_blocked`](pm.md)
        * [`/set_admin`](admin.md)
