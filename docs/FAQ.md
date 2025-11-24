# 常见问题解答

## 📦 包发布相关问题

### Q1: 如果我改东西了，需要重新发布吗？

**答案：取决于使用方式**

#### 情况1: 使用本地代码（开发模式）

```json
{
  "mcpServers": {
    "mobile-automation": {
      "command": "python",
      "args": ["/绝对路径/to/douzi-ai/backend/mobile_mcp/mcp/mcp_server.py"]
    }
  }
}
```

**不需要重新发布** ✅
- 代码修改后立即生效
- 适合开发和调试

#### 情况2: 使用pip安装的包（生产模式）

```json
{
  "mcpServers": {
    "mobile-automation": {
      "command": "python",
      "args": ["-m", "mobile_mcp.mcp.mcp_server"]
    }
  }
}
```

**需要重新发布** ⚠️
- 修改代码后需要：
  1. 更新版本号（setup.py）
  2. 重新构建包：`python -m build`
  3. 发布到PyPI：`twine upload dist/*`
  4. 用户更新：`pip install --upgrade mobile-mcp-ai`

### 推荐方案

- **开发阶段**：使用本地代码路径（方式1）
- **团队使用**：使用pip包 + 版本管理（方式2）

## 🔌 真机连接问题

### Q2: 在Cursor里面配置了MCP，执行的时候连接了真机也可以吗？

**答案：完全可以！** ✅

### 工作原理

```
┌─────────┐
│ Cursor  │
│   AI    │
└────┬────┘
     │ stdio通信（本地）
     ▼
┌─────────────────┐
│  MCP Server     │ ← 运行在你的电脑上
│  (你的电脑)      │
└────┬────────────┘
     │ ADB/WebDriverAgent
     ▼
┌─────────┐
│  真机   │ ← USB或WiFi连接
│/模拟器  │
└─────────┘
```

### 配置示例

#### Android真机（USB连接）

```json
{
  "mcpServers": {
    "mobile-automation": {
      "command": "python",
      "args": ["-m", "mobile_mcp.mcp.mcp_server"],
      "env": {
        "MOBILE_DEVICE_ID": "auto"  // 自动选择第一个设备
      }
    }
  }
}
```

**步骤**：
1. USB连接Android真机
2. 启用USB调试
3. 运行 `adb devices` 确认设备可见
4. Cursor会自动使用该设备

#### Android真机（WiFi连接）

```bash
# 1. 先用USB连接，开启WiFi调试
adb tcpip 5555

# 2. 连接WiFi（设备IP: 192.168.1.100）
adb connect 192.168.1.100:5555

# 3. 可以断开USB，使用WiFi
adb disconnect  # 断开USB
```

```json
{
  "env": {
    "MOBILE_DEVICE_ID": "192.168.1.100:5555"
  }
}
```

#### iOS真机

```json
{
  "mcpServers": {
    "mobile-automation": {
      "command": "python",
      "args": ["-m", "mobile_mcp.mcp.mcp_server"],
      "env": {
        "DEFAULT_PLATFORM": "ios",
        "MOBILE_DEVICE_ID": "auto"
      }
    }
  }
}
```

**步骤**：
1. USB连接iPhone/iPad
2. 在设备上信任电脑
3. 确保WebDriverAgent已安装并运行
4. Cursor会自动使用该设备

### 验证连接

```python
# 在Cursor中测试
@mobile_list_devices

# 应该能看到你的真机设备
```

## 🎯 其他常见问题

### Q3: 如何切换设备？

**方法1: 环境变量**

```json
{
  "env": {
    "MOBILE_DEVICE_ID": "emulator-5554"  // 指定设备ID
  }
}
```

**方法2: 代码中指定**

```python
from mobile_mcp.core.mobile_client import MobileClient

# 指定设备ID
client = MobileClient(device_id="emulator-5554")
```

### Q4: 如何同时支持Android和iOS？

**方法1: 使用环境变量切换**

```json
{
  "env": {
    "DEFAULT_PLATFORM": "android"  // 或 "ios"
  }
}
```

**方法2: 创建两个MCP Server配置**

```json
{
  "mcpServers": {
    "mobile-android": {
      "command": "python",
      "args": ["-m", "mobile_mcp.mcp.mcp_server"],
      "env": {
        "DEFAULT_PLATFORM": "android"
      }
    },
    "mobile-ios": {
      "command": "python",
      "args": ["-m", "mobile_mcp.mcp.mcp_server"],
      "env": {
        "DEFAULT_PLATFORM": "ios"
      }
    }
  }
}
```

### Q5: AI增强功能不可用怎么办？

**检查步骤**：

1. **检查AI增强是否启用**
```python
from mobile_mcp.config import Config
print(Config.is_ai_enhancement_enabled())  # 应该是True
```

2. **检查AI平台**
```python
from mobile_mcp.core.ai.ai_platform_adapter import get_ai_adapter
adapter = get_ai_adapter()
print(adapter.get_platform_name())
print(adapter.is_vision_available())
```

3. **如果不可用**
- 检查环境变量：`AI_ENHANCEMENT_ENABLED=true`
- 检查是否有可用的AI平台（Cursor、Claude等）
- 如果都不可用，会自动降级到基础功能

### Q6: 如何更新到最新版本？

**使用pip包**：
```bash
pip install --upgrade mobile-mcp-ai
```

**使用本地代码**：
```bash
cd /path/to/douzi-ai/backend/mobile_mcp
git pull
```

### Q7: 支持哪些AI平台？

- ✅ **Cursor AI**（免费，自动检测）
- ✅ **Claude**（需要API密钥：`ANTHROPIC_API_KEY`）
- ✅ **OpenAI GPT-4V**（需要API密钥：`OPENAI_API_KEY`）
- ✅ **Google Gemini**（需要API密钥：`GOOGLE_API_KEY`）

### Q8: 如何查看所有可用工具？

在Cursor中：
```
@mobile_snapshot  // 查看页面结构
@mobile_list_devices  // 查看设备列表
@mobile_list_apps  // 查看应用列表
```

或查看文档：`docs/COMPLETE_FEATURES.md`

## 📚 更多帮助

- [完整功能列表](COMPLETE_FEATURES.md)
- [使用指南](USAGE_COMBINED.md)
- [iOS设置指南](IOS_SETUP.md)
- [包发布指南](PACKAGE_PUBLISH.md)

