# Mobile MCP AI - 移动端自动化测试框架

## 🎉 已发布到 PyPI！

现在任何人都可以通过 PyPI 安装使用：

```bash
pip install mobile-mcp-ai
```

**PyPI 页面**：https://pypi.org/project/mobile-mcp-ai/

## 🚀 快速开始（PyPI 安装）

### 1. 安装包

```bash
pip install mobile-mcp-ai
```

### 2. 配置 Cursor

创建 `.cursor/mcp.json`：

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

### 3. 重启 Cursor 并开始使用

详细配置说明请查看：[Cursor 配置指南](CURSOR_SETUP.md)

---

## 📁 目录结构

```
backend/mobile_mcp/
├── core/                    # 核心功能模块
│   ├── locator/            # 定位器（包括Cursor AI视觉识别）
│   ├── ai/                 # AI分析模块
│   ├── assertion/          # 断言模块
│   ├── h5/                 # H5处理模块
│   ├── device_manager.py   # 设备管理
│   └── mobile_client.py    # 移动端客户端
│
├── mcp/                    # MCP服务器相关
│   └── mcp_server.py       # MCP服务器（Cursor AI工具）
│
├── examples/               # 测试示例
│   └── test_*.py          # 各种测试用例
│
├── screenshots/            # 截图目录
│   ├── requests/          # 分析请求文件（JSON）
│   └── results/           # 分析结果文件（JSON，由Cursor AI写入）
│
├── docs/                   # 文档目录
│   ├── md/                # Markdown文档
│   └── *.txt             # 其他文档
│
├── workspace/              # 工作区配置
│   └── *.code-workspace   # VS Code工作区文件
│
├── tools/                  # 工具脚本
├── utils/                  # 工具函数
├── vision/                 # 视觉识别模块
├── tests/                  # 测试文件
└── requirements.txt        # 依赖列表
```

## 🎯 核心功能

### 1. 智能定位系统
- 规则匹配（免费，85%）
- XML深度分析（免费，5%）
- 位置分析（免费，5%）
- 视觉识别（付费，4%）
- **Cursor AI视觉识别（免费，1%）** ⭐ 新增

### 2. Cursor AI自动视觉识别
- 自动截图（智能区域选择）
- 自动创建分析请求
- Cursor AI自动分析
- 自动获取坐标并点击
- 自动更新脚本

## 📖 文档

- **[📘 使用指南（推荐）](USAGE.md)** - 完整的安装和使用说明
- **[🌐 局域网共享部署](DEPLOY.md)** - HTTP服务器部署指南（方案2）
- [完整流程指南](docs/md/CURSOR_AI_COMPLETE_GUIDE.md)
- [使用说明](docs/md/CURSOR_AI_VISION_USAGE.md)
- [MCP设置](docs/md/CURSOR_MCP_SETUP.md)

## 🚀 快速开始（开发模式）

如果你想从源码运行或开发：

### 1. 安装依赖

```bash
cd backend/mobile_mcp
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -e .  # 以开发模式安装
```

### 2. 配置 Cursor

在 Cursor Settings 中添加 MCP Server 配置：

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
adb devices
```

### 4. 重启 Cursor 并开始使用

重启 Cursor 后，直接用自然语言告诉 AI：

```
打开 com.im30.way，点击登录按钮
```

详细说明请查看 [使用指南](USAGE.md)

---

## 🌐 局域网共享（HTTP Server）

如果你想在局域网内共享MCP服务，让其他人无需安装依赖：

### 快速启动

```bash
cd backend/mobile_mcp

# 安装HTTP服务器依赖
pip install fastapi uvicorn

# 启动服务器
python mcp/mcp_http_server.py

# 或使用启动脚本（自动获取IP）
./start_http_server.sh
```

服务器启动后会显示你的IP地址，其他人可以通过HTTP API访问。

详细说明请查看 [部署指南](DEPLOY.md)

## 🚀 快速开始（旧版）

```bash
cd backend/mobile_mcp
source venv/bin/activate
python examples/test_设置切换语言_完整版.py
```

## 📝 使用示例

当定位失败时，系统会自动：
1. 截图并创建请求文件
2. 等待Cursor AI分析（最多30秒）
3. 在Cursor中调用：`@mobile_analyze_screenshot request_id="xxx"`
4. Cursor AI分析并写入结果文件
5. 测试脚本继续执行


