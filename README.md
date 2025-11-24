<div align="center">

# 🚀 Mobile MCP AI

### 让 AI 帮你写移动端测试代码

> **🤖 用自然语言描述测试流程，AI 自动执行并生成 pytest 测试用例！**

[![PyPI version](https://img.shields.io/pypi/v/mobile-mcp-ai.svg)](https://pypi.org/project/mobile-mcp-ai/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)

[📖 启动指南](docs/START_GUIDE.md) • [🚀 快速开始](#-快速开始) • [💡 使用技巧](#-使用技巧) • [🤝 贡献](#-贡献)

---

</div>

## ✨ 核心优势

<div align="center">

### 🎯 **零代码编写，自然语言测试**
在 Cursor 中直接用自然语言描述测试流程，AI 自动理解并执行每一步操作  
**执行完成后，一键生成 pytest 格式的测试脚本** ⭐

### 🧠 **智能定位，自动重试**
找不到元素？AI 自动截图分析  
定位失败？自动尝试多种定位策略  
操作失败？AI 智能重试并调整策略

### 📝 **操作即代码，自动生成测试用例**
执行完测试流程后，AI 自动生成 pytest 测试脚本  
使用已验证的定位方式（坐标、bounds 等）  
**生成的脚本 100% 可执行，支持 pytest 批量运行和 Allure 报告**

</div>

---

## 🎉 已发布到 PyPI！

<div align="center">

```bash
pip install mobile-mcp-ai
```

**📦 PyPI**: [mobile-mcp-ai](https://pypi.org/project/mobile-mcp-ai/)  
**🐙 GitHub**: [test111ddff-hash/mobile-mcp-ai](https://github.com/test111ddff-hash/mobile-mcp-ai)

</div>

---

## 🚀 快速开始

### 1️⃣ 安装包

```bash
pip install mobile-mcp-ai
```

### 2️⃣ 配置 Cursor MCP

创建 `.cursor/mcp.json`（项目根目录或用户目录 `~/.cursor/mcp.json`）：

<details>
<summary>📋 点击查看配置示例</summary>

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

</details>

**详细配置说明请查看：** [📖 启动指南](docs/START_GUIDE.md)

### 3️⃣ 连接设备并重启 Cursor

```bash
# 连接 Android 设备
adb devices  # 确认设备可见
```

**重要：** 配置完成后，必须完全退出并重新启动 Cursor！

### 4️⃣ 开始使用

重启 Cursor 后，直接在聊天窗口说：

```
帮我测试登录功能：
1. 启动 com.example.app
2. 点击登录按钮
3. 输入用户名 admin
4. 输入密码 password
5. 点击提交按钮
```

<div align="center">

**✨ AI 会自动执行每一步操作！**

</div>

---

## 🎯 核心功能演示

### 📱 自然语言执行测试

<div align="center">

**💬 你说：**

</div>

```
帮我测试发帖功能：
1. 启动 com.im30.way
2. 点击底部第三个图标
3. 点击黄色+号按钮
4. 输入内容"这是一条测试内容"
5. 点击提交按钮
```

<div align="center">

**🤖 AI 自动执行每一步操作！**

</div>

---

### 📝 执行后自动生成 pytest 用例 ⭐

<div align="center">

**💬 执行完测试后，你说：**

</div>

```
帮我生成 pytest 测试脚本，测试名称是"建议发帖测试"，包名是 com.im30.way，文件名是 test_建议发帖
```

<div align="center">

**🤖 AI 自动生成标准的 pytest 格式测试脚本！**

</div>

**生成的脚本可以直接运行：**

```bash
pytest tests/test_建议发帖.py -v
```

---

## 💡 使用技巧

### 💡 技巧 1：生成测试脚本的最佳时机

1. ✅ 先用自然语言执行一遍完整的测试流程
2. ✅ 确保所有操作都成功执行
3. ✅ 然后让 AI 生成 pytest 脚本

### 💡 技巧 2：智能定位失败时的处理

如果 AI 找不到元素，会自动：
1. 📸 截图并创建分析请求
2. 🧠 调用 Cursor AI 视觉识别
3. 📍 获取坐标并点击
4. ✅ 继续执行后续步骤

### 💡 技巧 3：批量生成测试脚本

执行多个测试流程后，可以批量生成 pytest 脚本。

---

## 🎯 为什么选择 Mobile MCP AI？

<div align="center">

| 特性 | 传统方式 | Mobile MCP AI |
|:----:|:--------:|:-------------:|
| **编写测试** | ❌ 需要写代码 | ✅ 自然语言描述 ✨ |
| **定位元素** | ❌ 手动写定位器 | ✅ AI 智能定位 ✨ |
| **调试失败** | ❌ 手动分析日志 | ✅ AI 自动分析 ✨ |
| **生成脚本** | ❌ 手动编写 | ✅ AI 自动生成 ✨ |
| **代码复用** | ❌ 需要手动提取 | ✅ 自动生成 pytest ✨ |
| **学习曲线** | ❌ 需要学习 API | ✅ 自然语言即可 ✨ |

</div>

---

## 🌟 核心优势

### 1. **零代码编写** 🎨
- ✨ 不需要学习任何 API
- ✨ 直接用自然语言描述测试流程
- ✨ AI 自动理解并执行

### 2. **智能定位系统** 🧠
- 📊 规则匹配（85%）
- 🔍 XML 深度分析（5%）
- 📍 位置分析（5%）
- **🎯 Cursor AI 视觉识别（免费，1%）** ⭐

### 3. **操作即代码** 📝
- ✨ 执行完测试后，一键生成 pytest 脚本
- ✨ 使用已验证的定位方式
- ✨ 100% 可执行的测试代码

### 4. **智能调试** 🔧
- ✨ 失败时自动截图分析
- ✨ AI 自动调整策略
- ✨ 自动重试和错误处理

---

## 📚 详细文档

<div align="center">

| 📖 文档 | 📝 说明 |
|--------|--------|
| [🚀 启动指南](docs/START_GUIDE.md) | **完整的安装和配置步骤** |
| [📘 使用指南](docs/INSTALL_AND_USE.md) | 详细的使用说明 |
| [❓ 常见问题](docs/FAQ.md) | FAQ 和故障排除 |
| [🍎 iOS 设置](docs/IOS_SETUP.md) | iOS 设备配置指南 |

</div>

---

## 🚀 开始使用

<div align="center">

```bash
# 1. 安装
pip install mobile-mcp-ai

# 2. 配置 Cursor（创建 .cursor/mcp.json）
# 3. 连接设备（adb devices）
# 4. 重启 Cursor
# 5. 开始用自然语言测试！
```

**🎉 现在就试试吧！**

</div>

---

## 📄 License

<div align="center">

**Apache License 2.0**

</div>

---

## 🤝 贡献

<div align="center">

欢迎提交 Issue 和 Pull Request！

**🐙 GitHub 仓库**: [test111ddff-hash/mobile-mcp-ai](https://github.com/test111ddff-hash/mobile-mcp-ai)

---

**⭐ 如果这个项目对你有帮助，请给个 Star！⭐**

Made with ❤️ by [douzi](https://github.com/test111ddff-hash)

</div>
