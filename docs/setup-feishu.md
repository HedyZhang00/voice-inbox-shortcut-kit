# 配置飞书

## 1. 创建多维表格

推荐直接复制公开模板。模板尚未发布时，可按
[`templates/feishu-base-schema.json`](../templates/feishu-base-schema.json)
中的字段创建一个空白多维表格。

模板只能包含字段、选项和示例说明，不应包含任何真实灵感记录。

## 2. 创建企业自建应用

在飞书开放平台创建一个企业自建应用，例如“灵感快收助手”。

只开通向指定多维表格新增记录所需的权限，不申请通讯录、消息、审批等无关权限。
在飞书开放平台的权限管理页搜索“多维表格”和“新增记录”，以页面显示的当前权限名称为准。

应用发布后，将应用添加为目标多维表格的协作者，并授予可编辑权限。

飞书官方接口：

- 获取自建应用 `tenant_access_token`
- `POST /open-apis/bitable/v1/apps/:app_token/tables/:table_id/records`

## 3. 准备配置

复制配置示例：

```bash
cp config/feishu_config.example.json config/feishu_config.json
```

填写：

- `app_id`
- `app_token`
- `table_id`
- 苹果提醒事项列表名称
- 苹果日历名称

不要把 App Secret 写进这个 JSON。

## 4. 把 App Secret 存入 macOS 钥匙串

```bash
security add-generic-password \
  -U \
  -s "linggan-voice-inbox.feishu" \
  -a "你的 App ID" \
  -w
```

命令会在终端中安全询问 Secret。完成后，将配置里的
`app_secret_keychain_account` 改为同一个 App ID。

## 5. 权限验证

如果接口返回无权限：

1. 确认自建应用已发布。
2. 确认应用具有新增多维表格记录的权限。
3. 确认应用已成为目标多维表格的可编辑协作者。
4. 确认 `app_token`、`table_id` 来自正确的表。
