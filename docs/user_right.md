# 用户权限
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
* [trusted](trusted.md) 用户
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
* [admin](admin.md) 用户
    * 可以使用 trusted 用户可使用的指令
    * 于群组中可以使用：
        * `/set_voter`
        * `/list_voter`
        * `/unset_voter`
        * `/init_poll`
        * `/start_poll`
        * 点按关闭投票按钮
    * 于私聊中可以使用：
        * `/set_voter`
        * `/unset_voter`
* [voter](voter.md) 用户
    * 于群组中可以使用：
        * 点按投票选项
* operator （机器人操作者）
    * 可以使用所有用户均可使用的指令
    * 可以使用 trusted 用户可使用的指令
    * 可以使用 admin 用户可使用的指令
    * 于群组中可以使用：
        * `/set_admin`
    * 于私聊中可以使用：
        * `/reply`
        * `/block`
        * `/unblock`
        * `/list_blocked`
        * `/set_admin`
