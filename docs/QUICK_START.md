# 快速开始指南

## 🚀 5分钟快速上手

### 1. 安装

```bash
# 方式1: pip安装（推荐）
pip install mobile-mcp-ai

# 方式2: 本地安装（开发模式）
cd backend/mobile_mcp
pip install -e .
```

### 2. 连接设备

#### Android

```bash
# USB连接真机或启动模拟器
adb devices  # 确认设备可见
```

#### iOS（macOS only）

```bash
# 列出模拟器
xcrun simctl list devices

# 启动模拟器
xcrun simctl boot "iPhone 15"
```

### 3. 配置Cursor

创建 `.cursor/mcp.json`：

```json
{
  "mcpServers": {
    "mobile-automation": {
      "command": "python",
      "args": ["-m", "mobile_mcp.mcp.mcp_server"],
      "env": {
        "MOBILE_DEVICE_ID": "auto",
        "AI_ENHANCEMENT_ENABLED": "true"
      }
    }
  }
}
```

### 4. 开始使用

在Cursor中直接说：

```
帮我测试登录功能：
1. 启动 com.example.app
2. 点击登录按钮
3. 输入用户名 admin
4. 输入密码 password
5. 点击提交
```

## 📱 真机连接

### Android真机

**USB连接**：
1. USB连接手机
2. 启用USB调试
3. 运行 `adb devices` 确认
4. Cursor自动使用真机 ✅

**WiFi连接**：
```bash
# 先用USB开启WiFi调试
adb tcpip 5555

# WiFi连接
adb connect <设备IP>:5555

# Cursor配置
{
  "env": {
    "MOBILE_DEVICE_ID": "<设备IP>:5555"
  }
}
```

### iOS真机

1. USB连接iPhone
2. 在设备上信任电脑
3. 确保WebDriverAgent已安装
4. Cursor自动使用真机 ✅

## 🔧 常见问题

### Q: 改代码后需要重新发布吗？

**本地代码**：不需要 ✅
```json
{
  "args": ["/绝对路径/to/mcp_server.py"]
}
```

**pip包**：需要 ⚠️
```bash
# 更新版本号后重新发布
python -m build
twine upload dist/*
```

### Q: 真机可以使用吗？

**完全可以！** ✅

MCP Server运行在你的电脑上，通过ADB/WebDriverAgent连接真机。

## 📚 更多文档

- [完整使用指南](USAGE_COMBINED.md)
- [常见问题](FAQ.md)
- [iOS设置](IOS_SETUP.md)
- [包发布](PACKAGE_PUBLISH.md)

