# 灵感快收：iPhone 语音收件箱

一个低打扰的 iPhone Action 键语音收件箱。

长按 Action 键后直接开始中文语音听写，手动结束后只出现一个可编辑文本框。
内容会由 iPhone 直接写入飞书多维表格；明确的待办和日程还会进入苹果提醒事项或日历。

日常使用不依赖 Mac 开机、不依赖同一个 Wi-Fi，也不需要额外云服务器。

## 使用体验

```text
Action 键
-> 中文语音听写
-> 手动结束
-> 在唯一文本框中修正识别结果
-> 飞书统一收件箱
-> 必要时写入苹果提醒事项或日历
```

固定产品规则见 [`docs/product-spec.md`](docs/product-spec.md)。

## 仓库包含什么

- 可审查的快捷指令生成器
- 飞书多维表格空白模板结构
- 飞书自建应用 OpenAPI 配置说明
- iPhone 安装和验收说明
- 安全与密钥撤销说明

## 为什么不直接提供 `.shortcut`

本项目采用 iPhone 直连飞书 OpenAPI。每个使用者都需要自己的飞书应用和表格配置，
生成后的快捷指令会包含这些私人凭证。

因此仓库公开生成器，不公开任何人生成后的 `.shortcut` 文件。

## 快速开始

1. [打开并复制飞书空白模板](https://my.feishu.cn/base/FURsb8sKgaNT5Fst1daccGVnnld)，或参见 [`docs/setup-feishu.md`](docs/setup-feishu.md) 手动建表。
2. 复制 `config/feishu_config.example.json` 为 `config/feishu_config.json`。
3. 把 App Secret 存入 macOS 钥匙串。
4. 运行生成器并导入 iPhone，参见 [`docs/setup-iphone.md`](docs/setup-iphone.md)。

## 飞书接口

快捷指令每次运行调用两个接口：

1. 获取自建应用 `tenant_access_token`。
2. 新增一条多维表格记录。

新增记录接口可查看[飞书开放平台官方文档](https://open.feishu.cn/document/server-docs/docs/bitable-v1/app-table-record/create)。

## 开源边界

可以公开：

- 源码
- 字段模板
- 空白配置示例
- 产品规则和安装教程

不能公开：

- App Secret
- 私人 `app_token` 和 `table_id`
- 生成后的 `.shortcut`
- 真实飞书记录

完整说明见 [`SECURITY.md`](SECURITY.md)。

## 当前限制

- 第一版使用本机关键词区分普通灵感、提醒事项和日程，不调用 AI 分类接口。
- 生成步骤需要 Mac；安装后日常采集不需要 Mac。
- 飞书在线模板只包含字段结构，不包含任何私人记录。

## License

MIT
