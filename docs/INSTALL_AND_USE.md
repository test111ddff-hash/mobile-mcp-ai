# 安装和使用指南（发布后）

## 🎯 发布后别人如何使用

### ✅ 是的！发布后别人就可以在Cursor中配置MCP了

## 📦 安装步骤

### 步骤1: 安装包

```bash
# 基础安装
pip install mobile-mcp-ai

# 或完整安装（包含所有功能）
pip install mobile-mcp-ai[all]
```

### 步骤2: 配置Cursor

创建 `.cursor/mcp.json` 文件：

**位置**：
- 项目根目录：`/path/to/project/.cursor/mcp.json`
- 或用户目录：`~/.cursor/mcp.json`

**配置内容**：

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

### 步骤3: 重启Cursor

重启Cursor后，MCP Server会自动启动。

### 步骤4: 开始使用

在Cursor中直接说：

```
帮我测试登录功能：
1. 启动 com.example.app
2. 点击登录按钮
3. 输入用户名 admin
4. 输入密码 password
5. 点击提交按钮
```

## 🔧 配置说明

### 基础配置（最简单）

```json
{
  "mcpServers": {
    "mobile-automation": {
      "command": "python",
      "args": ["-m", "mobile_mcp.mcp.mcp_server"],
      "env": {
        "MOBILE_DEVICE_ID": "auto"
      }
    }
  }
}
```

### 完整配置（推荐）

```json
{
  "mcpServers": {
    "mobile-automation": {
      "command": "python",
      "args": ["-m", "mobile_mcp.mcp.mcp_server"],
      "env": {
        "MOBILE_DEVICE_ID": "auto",
        "AI_ENHANCEMENT_ENABLED": "true",
        "DEFAULT_PLATFORM": "android",
        "LOCK_SCREEN_ORIENTATION": "true"
      }
    }
  }
}
```

## 📱 真机连接

### Android真机

**USB连接**：
1. USB连接手机
2. 启用USB调试
3. 运行 `adb devices` 确认设备可见
4. Cursor会自动使用真机 ✅

**WiFi连接**：
```bash
# 先用USB开启WiFi调试
adb tcpip 5555
adb connect <设备IP>:5555
```

```json
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

```json
{
  "env": {
    "DEFAULT_PLATFORM": "ios",
    "MOBILE_DEVICE_ID": "auto"
  }
}
```

## ✅ 验证安装

### 1. 检查包是否安装

```bash
pip show mobile-mcp-ai
```

### 2. 检查模块是否可用

```bash
python -c "from mobile_mcp.core.mobile_client import MobileClient; print('✅ 安装成功')"
```

### 3. 在Cursor中测试

重启Cursor后，说：

```
@mobile_list_devices
```

应该能看到设备列表。

## 🎯 使用示例

### 示例1: 基础自动化

```
帮我测试登录：
1. 启动 com.example.app
2. 点击登录按钮
3. 输入用户名 admin
4. 输入密码 password
5. 点击提交
```

### 示例2: 游戏自动化

```
帮我测试游戏：
1. 启动 com.game.example
2. 点击开始游戏按钮（使用视觉识别）
3. 等待3秒
4. 点击确认按钮
```

### 示例3: 复杂流程

```
帮我完成以下操作：
1. 启动 com.example.app
2. 点击底部导航栏的"我的"
3. 点击设置
4. 切换到English语言
5. 返回首页
6. 验证页面是否显示英文
```

## 🔄 更新包

```bash
# 更新到最新版本
pip install --upgrade mobile-mcp-ai

# 重启Cursor
```

## 📋 前置要求

### Android

- ✅ Python 3.8+
- ✅ ADB（Android SDK Platform Tools）
- ✅ 已连接Android设备或模拟器
- ✅ uiautomator2（pip会自动安装）

### iOS（可选）

- ✅ macOS系统
- ✅ Xcode Command Line Tools
- ✅ WebDriverAgent（需要单独安装）

## 🎉 总结

**发布后，别人只需要**：

1. `pip install mobile-mcp-ai` ✅
2. 配置 `.cursor/mcp.json` ✅
3. 重启Cursor ✅
4. 开始使用！🚀

**完全不需要了解代码细节！**

