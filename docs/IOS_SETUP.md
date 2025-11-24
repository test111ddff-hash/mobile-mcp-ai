# iOS支持设置指南

## 📱 前置要求

### 1. macOS系统
iOS自动化只能在macOS上运行（需要Xcode）

### 2. 安装Xcode Command Line Tools

```bash
xcode-select --install
```

### 3. 安装WebDriverAgent（推荐）

```bash
# 克隆WebDriverAgent
git clone https://github.com/appium/WebDriverAgent.git
cd WebDriverAgent

# 安装依赖
./Scripts/bootstrap.sh

# 在Xcode中打开项目
open WebDriverAgent.xcworkspace
```

### 4. 安装Appium（备选方案）

```bash
npm install -g appium
npm install -g @appium/ios-driver
```

## 🔧 配置设备

### iOS模拟器

```bash
# 列出所有模拟器
xcrun simctl list devices

# 启动模拟器
xcrun simctl boot "iPhone 15"

# 打开模拟器
open -a Simulator
```

### iOS真机

1. **连接设备**
   - USB连接iPhone/iPad
   - 在设备上信任电脑

2. **安装libimobiledevice**（可选，用于检测真机）

```bash
brew install libimobiledevice

# 检测真机
idevice_id -l
```

3. **配置WebDriverAgent**
   - 在Xcode中打开WebDriverAgent项目
   - 修改Signing & Capabilities（使用你的Apple ID）
   - 在设备上安装WebDriverAgent

## 🚀 使用示例

### Python代码

```python
from mobile_mcp.core.mobile_client import MobileClient

# 创建iOS客户端
client = MobileClient(platform="ios", device_id=None)

# 启动应用
await client.launch_app("com.example.app")

# 点击元素
await client.click("登录按钮")
```

### MCP配置

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

## ⚠️ 注意事项

1. **WebDriverAgent需要签名**
   - 使用免费Apple ID即可
   - 需要在Xcode中配置Signing

2. **真机需要信任**
   - 首次连接需要在设备上点击"信任"

3. **网络连接**
   - WebDriverAgent默认运行在localhost:8100
   - 确保端口未被占用

4. **权限问题**
   - iOS自动化需要辅助功能权限
   - 首次运行时需要在设置中授权

## 🔍 故障排除

### 问题1: 找不到设备

```bash
# 检查模拟器
xcrun simctl list devices

# 检查真机
idevice_id -l
```

### 问题2: WebDriverAgent连接失败

```bash
# 检查WebDriverAgent是否运行
lsof -i :8100

# 手动启动WebDriverAgent
cd WebDriverAgent
xcodebuild -project WebDriverAgent.xcodeproj \
  -scheme WebDriverAgentRunner \
  -destination 'id=<设备ID>' test
```

### 问题3: 权限问题

- 在iOS设备上：设置 → 通用 → 辅助功能 → 启用WebDriverAgent

## 📚 参考资源

- [WebDriverAgent文档](https://github.com/appium/WebDriverAgent)
- [Appium iOS文档](https://github.com/appium/appium-xcuitest-driver)
- [XCUITest文档](https://developer.apple.com/documentation/xctest)

