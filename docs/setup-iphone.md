# 生成并安装 iPhone 快捷指令

## 1. 环境

需要一台 Mac，用来生成和签名私人快捷指令。快捷指令安装到 iPhone 后，日常使用不依赖 Mac。

## 2. 验证公开生成器

```bash
python3 scripts/generate_shortcut.py \
  --config config/feishu_config.example.json \
  --validate-only
```

正确结果应为：

```json
{
  "dictation": 1,
  "editable_text_box": 1,
  "notification": 0,
  "file_actions": 0
}
```

## 3. 生成私人快捷指令

完成飞书配置和钥匙串设置后运行：

```bash
python3 scripts/generate_shortcut.py
```

文件会生成到 `dist/灵感快收.shortcut`。

这个文件包含个人飞书配置，不能上传 GitHub，也不能直接公开分享。

## 4. 导入 iPhone

1. 在 Mac 上打开生成的 `.shortcut` 文件。
2. 添加到快捷指令 App。
3. 通过 iCloud 同步到 iPhone。
4. 在 iPhone 设置中把 Action 键绑定到“灵感快收”。
5. 第一次运行时允许语音识别、提醒事项和日历权限。

系统权限提示由 iOS 控制。稳定安装后不要频繁删除和重新导入快捷指令。

## 5. 验收

在关闭 Wi-Fi、使用手机流量的情况下测试：

1. Mac 休眠。
2. 长按 Action 键。
3. 说一条普通灵感并手动结束。
4. 在唯一文本框里检查文字并完成。
5. 确认飞书新增记录。

再分别测试一条提醒事项和一条日程安排。
