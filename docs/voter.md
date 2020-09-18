# Voter

voter 用户由 [admin](admin.md) 用户授权，可以在[投票](poll.md)中点按选项。voter 用户权限仅限单个群组，每个群组需单独授予权限。

## 权限管理指令

### /set_voter

admin 用户在群组中使用，于当前群组授予用户 voter 权限。使用方法：

回复需要授予 voter 的用户，内容为 `/set_voter`

或

```
/set_voter <用户ID> <用户ID> ...
```

### /list_voter

admin 用户在群组中使用，列出当前群组中的 voter 用户。

### /unset_voter

admin 用户在群组中使用，移除当前群组中用户的 voter 权限。使用方法：

回复需要移除 voter 权限的用户，内容为 `/unset_voter`

或

```
/unset_voter <用户ID> <用户ID> ...
```
