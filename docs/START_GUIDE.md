# 🚀 Mobile MCP AI 启动指南

## 📋 目录

- [快速开始](#快速开始)
- [详细步骤](#详细步骤)
- [验证安装](#验证安装)
- [常见问题](#常见问题)

---

## 🚀 快速开始

### 1. 安装包

```bash
pip install mobile-mcp-ai
```

### 2. 配置 Cursor

创建 `.cursor/mcp.json` 文件（项目根目录或用户目录 `~/.cursor/mcp.json`）：

```json
{
  "mcpServers": {
    "mobile-mcp-ai": {
      "command": "python",
      "args": ["-m", "mobile_mcp.mcp.mcp_server"],
      "env": {
        "MOBILE_DEVICE_ID": "auto"
      }
    }
  }
}
```

### 3. 连接设备

```bash
# Android 设备
adb devices  # 确认设备可见

# iOS 设备（macOS only）
xcrun simctl list devices  # 列出模拟器
```

### 4. 重启 Cursor

完全退出并重新启动 Cursor，MCP 服务器会自动启动。

### 5. 开始使用

在 Cursor 聊天窗口中说：

```
帮我测试登录功能：
1. 启动 com.example.app
2. 点击登录按钮
3. 输入用户名 admin
4. 输入密码 password
5. 点击提交按钮
```

---

## 📝 详细步骤

### 步骤 1：安装包

#### 方式 A：从 PyPI 安装（推荐）

```bash
pip install mobile-mcp-ai
```

#### 方式 B：从源码安装

```bash
git clone https://github.com/test111ddff-hash/mobile-mcp-ai.git
cd mobile-mcp-ai
pip install -e .
```

#### 方式 C：安装完整版本（包含所有功能）

```bash
pip install mobile-mcp-ai[all]
```

### 步骤 2：配置 Cursor

#### 配置文件位置

**选项 1：项目根目录**（推荐用于项目特定配置）
```
/path/to/your/project/.cursor/mcp.json
```

**选项 2：用户目录**（推荐用于全局配置）
```
~/.cursor/mcp.json
```

#### 基础配置

```json
{
  "mcpServers": {
    "mobile-mcp-ai": {
      "command": "python",
      "args": ["-m", "mobile_mcp.mcp.mcp_server"],
      "env": {
        "MOBILE_DEVICE_ID": "auto"
      }
    }
  }
}
```

#### 完整配置（推荐）

```json
{
  "mcpServers": {
    "mobile-mcp-ai": {
      "command": "python",
      "args": ["-m", "mobile_mcp.mcp.mcp_server"],
      "env": {
        "MOBILE_DEVICE_ID": "auto",
        "DEFAULT_PLATFORM": "android"
      }
    }
  }
}
```

#### 使用虚拟环境

如果使用虚拟环境，需要指定 Python 路径：

```json
{
  "mcpServers": {
    "mobile-mcp-ai": {
      "command": "/path/to/venv/bin/python",
      "args": ["-m", "mobile_mcp.mcp.mcp_server"],
      "env": {
        "MOBILE_DEVICE_ID": "auto"
      }
    }
  }
}
```

#### iOS 配置

```json
{
  "mcpServers": {
    "mobile-mcp-ai": {
      "command": "python",
      "args": ["-m", "mobile_mcp.mcp.mcp_server"],
      "env": {
        "MOBILE_DEVICE_ID": "auto",
        "DEFAULT_PLATFORM": "ios",
        "IOS_SUPPORT_ENABLED": "true"
      }
    }
  }
}
```

### 步骤 3：连接设备

#### Android 设备

**USB 连接：**
1. 用 USB 线连接手机到电脑
2. 在手机上启用"USB 调试"
3. 在手机上允许 USB 调试授权
4. 运行 `adb devices` 确认设备可见

**WiFi 连接：**
```bash
# 1. 先用 USB 连接，开启 WiFi 调试
adb tcpip 5555

# 2. WiFi 连接（替换为你的设备 IP）
adb connect 192.168.1.100:5555

# 3. 在配置中设置设备 ID
# "MOBILE_DEVICE_ID": "192.168.1.100:5555"
```

#### iOS 设备（macOS only）

**模拟器：**
```bash
# 列出可用模拟器
xcrun simctl list devices

# 启动模拟器
xcrun simctl boot "iPhone 15"
```

**真机：**
1. USB 连接 iPhone
2. 在设备上信任电脑
3. 确保 WebDriverAgent 已安装

### 步骤 4：重启 Cursor

**重要：** 配置完成后，必须完全退出并重新启动 Cursor，MCP 服务器才会加载新配置。

**macOS：**
- 使用 `Cmd + Q` 完全退出
- 或从菜单选择 "Quit Cursor"

**Windows/Linux：**
- 完全关闭 Cursor 应用
- 重新启动

### 步骤 5：开始使用

重启后，在 Cursor 聊天窗口中直接使用自然语言：

```
帮我测试登录功能：
1. 启动 com.example.app
2. 点击登录按钮
3. 输入用户名 admin
4. 输入密码 password
5. 点击提交按钮
6. 验证页面是否显示"欢迎"
```

---

## ✅ 验证安装

### 1. 检查包是否安装

```bash
pip show mobile-mcp-ai
```

应该显示：
```
Name: mobile-mcp-ai
Version: 1.0.1
...
```

### 2. 检查模块是否可用

```bash
python -c "from mobile_mcp.core.mobile_client import MobileClient; print('✅ 安装成功')"
```

### 3. 检查设备连接

```bash
# Android
adb devices

# iOS
xcrun simctl list devices
```

### 4. 在 Cursor 中测试

重启 Cursor 后，尝试：

```
列出所有连接的设备
```

如果配置正确，AI 应该能够调用 `mobile_list_devices` 工具并返回设备列表。

---

## ❓ 常见问题

### Q1: MCP 服务器未启动

**症状：** 在 Cursor 中无法使用移动端工具

**解决方法：**
1. 检查配置文件路径是否正确
2. 检查 Python 路径是否正确
3. 完全退出并重新启动 Cursor
4. 检查 Cursor 的 MCP 日志（如果有）

### Q2: 找不到设备

**症状：** `mobile_list_devices` 返回空列表

**解决方法：**
1. 运行 `adb devices` 确认设备可见
2. 检查设备是否已授权（状态应该是 `device`，不是 `unauthorized`）
3. 检查 `MOBILE_DEVICE_ID` 配置是否正确

### Q3: 导入错误

**症状：** `ModuleNotFoundError: No module named 'mobile_mcp'`

**解决方法：**
1. 确认包已正确安装：`pip show mobile-mcp-ai`
2. 如果使用虚拟环境，确保 Cursor 配置中的 Python 路径指向虚拟环境
3. 重新安装：`pip install --upgrade mobile-mcp-ai`

### Q4: 权限错误

**症状：** `Permission denied` 或 `403` 错误

**解决方法：**
1. 检查设备 USB 调试是否已启用
2. 在设备上确认 USB 调试授权
3. 尝试重新连接设备

### Q5: 配置不生效

**症状：** 修改配置后，MCP 服务器仍使用旧配置

**解决方法：**
1. **必须完全退出 Cursor**（不是关闭窗口）
2. 重新启动 Cursor
3. 检查配置文件语法是否正确（JSON 格式）

---

## 📚 下一步

- [使用指南](INSTALL_AND_USE.md) - 详细的使用说明
- [常见问题](FAQ.md) - 更多 FAQ
- [iOS 设置](IOS_SETUP.md) - iOS 设备配置

---

## 🆘 获取帮助

如果遇到问题：

1. 查看 [常见问题](FAQ.md)
2. 提交 [Issue](https://github.com/test111ddff-hash/mobile-mcp-ai/issues)
3. 查看 [GitHub 仓库](https://github.com/test111ddff-hash/mobile-mcp-ai)

---

<div align="center">

**🎉 配置完成后，开始享受 AI 驱动的移动端自动化测试吧！**

</div>

