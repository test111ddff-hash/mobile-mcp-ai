# 发布和使用指南

## 📦 发布流程

### 1. 准备发布

```bash
cd backend/mobile_mcp

# 1. 更新版本号
vim setup.py  # 修改 version="1.0.0" 为 "1.0.1"

# 2. 更新CHANGELOG（如果有）
# 3. 提交代码
git add .
git commit -m "Release v1.0.1"
git tag v1.0.1
git push origin master --tags
```

### 2. 构建包

```bash
# 安装构建工具
pip install build twine

# 清理旧的构建文件
rm -rf dist/ build/ *.egg-info

# 构建包
python -m build

# 检查构建结果
ls -lh dist/
# 应该看到：
# - mobile_mcp_enhanced-1.0.0.tar.gz
# - mobile_mcp_enhanced-1.0.0-py3-none-any.whl
```

### 3. 测试发布（TestPyPI）

```bash
# 注册TestPyPI账号：https://test.pypi.org/

# 配置凭据（~/.pypirc）
[testpypi]
username = __token__
password = pypi-your-test-token

# 上传到TestPyPI
twine upload --repository testpypi dist/*

# 测试安装
pip install --index-url https://test.pypi.org/simple/ mobile-mcp-ai
```

### 4. 正式发布（PyPI）

```bash
# 注册PyPI账号：https://pypi.org/

# 配置凭据（~/.pypirc）
[pypi]
username = __token__
password = pypi-your-production-token

# 上传到PyPI
twine upload dist/*

# 验证发布
pip install mobile-mcp-ai
```

## 🎯 发布后：别人如何使用

### 方式1: pip安装（推荐）

#### 步骤1: 安装包

```bash
# 基础安装
pip install mobile-mcp-ai

# 完整安装（包含所有功能）
pip install mobile-mcp-ai[all]

# 仅iOS支持
pip install mobile-mcp-ai[ios]

# 仅AI支持
pip install mobile-mcp-ai[ai]
```

#### 步骤2: 配置Cursor

创建 `.cursor/mcp.json`（在项目根目录或用户目录）：

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

#### 步骤3: 重启Cursor

重启Cursor后，MCP Server会自动启动。

#### 步骤4: 开始使用

在Cursor中直接说：

```
帮我测试登录功能：
1. 启动 com.example.app
2. 点击登录按钮
3. 输入用户名 admin
4. 输入密码 password
5. 点击提交按钮
```

### 方式2: 本地代码（开发模式）

如果别人想使用你的代码（未发布）：

#### 步骤1: 克隆代码

```bash
git clone https://github.com/yourusername/douzi-ai.git
cd douzi-ai/backend/mobile_mcp
pip install -r requirements.txt
```

#### 步骤2: 配置Cursor

```json
{
  "mcpServers": {
    "mobile-automation": {
      "command": "python",
      "args": ["/绝对路径/to/douzi-ai/backend/mobile_mcp/mcp/mcp_server.py"],
      "env": {
        "PYTHONPATH": "/绝对路径/to/douzi-ai",
        "MOBILE_DEVICE_ID": "auto",
        "AI_ENHANCEMENT_ENABLED": "true"
      }
    }
  }
}
```

## 🔧 配置说明

### 基础配置

```json
{
  "mcpServers": {
    "mobile-automation": {
      "command": "python",
      "args": ["-m", "mobile_mcp.mcp.mcp_server"],
      "env": {
        "MOBILE_DEVICE_ID": "auto",           // 设备ID（auto=自动选择）
        "AI_ENHANCEMENT_ENABLED": "true",     // 启用AI增强
        "DEFAULT_PLATFORM": "android"         // 平台（android/ios）
      }
    }
  }
}
```

### 高级配置

```json
{
  "mcpServers": {
    "mobile-automation": {
      "command": "python",
      "args": ["-m", "mobile_mcp.mcp.mcp_server"],
      "env": {
        "MOBILE_DEVICE_ID": "emulator-5554",           // 指定设备
        "AI_ENHANCEMENT_ENABLED": "true",
        "PREFERRED_AI_PLATFORM": "cursor",             // 优先AI平台
        "DEFAULT_PLATFORM": "android",
        "LOCK_SCREEN_ORIENTATION": "true",              // 锁定屏幕方向
        "SMART_LOCATOR_ENABLED": "true",                // 启用智能定位
        "H5_HANDLER_ENABLED": "true"                    // 启用H5处理
      }
    }
  }
}
```

### iOS配置

```json
{
  "mcpServers": {
    "mobile-ios": {
      "command": "python",
      "args": ["-m", "mobile_mcp.mcp.mcp_server"],
      "env": {
        "DEFAULT_PLATFORM": "ios",
        "IOS_SUPPORT_ENABLED": "true",
        "MOBILE_DEVICE_ID": "auto"
      }
    }
  }
}
```

## 📱 真机连接配置

### Android真机（USB）

```bash
# 1. USB连接手机
# 2. 启用USB调试
# 3. 运行 adb devices 确认设备可见

# Cursor配置（自动使用真机）
{
  "env": {
    "MOBILE_DEVICE_ID": "auto"  // 自动选择第一个设备
  }
}
```

### Android真机（WiFi）

```bash
# 1. USB连接开启WiFi调试
adb tcpip 5555

# 2. WiFi连接
adb connect 192.168.1.100:5555

# 3. Cursor配置
{
  "env": {
    "MOBILE_DEVICE_ID": "192.168.1.100:5555"
  }
}
```

### iOS真机

```bash
# 1. USB连接iPhone
# 2. 在设备上信任电脑
# 3. 确保WebDriverAgent已安装

# Cursor配置
{
  "env": {
    "DEFAULT_PLATFORM": "ios",
    "MOBILE_DEVICE_ID": "auto"
  }
}
```

## ✅ 验证安装

### 1. 检查安装

```bash
# 检查包是否安装
pip show mobile-mcp-ai

# 检查模块是否可用
python -c "from mobile_mcp.core.mobile_client import MobileClient; print('✅ 安装成功')"
```

### 2. 检查MCP Server

```bash
# 测试MCP Server能否启动
python -m mobile_mcp.mcp.mcp_server --help

# 或直接运行（会等待MCP协议输入）
python -m mobile_mcp.mcp.mcp_server
```

### 3. 在Cursor中测试

重启Cursor后，在Cursor中说：

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
2. 点击开始游戏按钮
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

### 用户更新

```bash
# 更新到最新版本
pip install --upgrade mobile-mcp-ai

# 重启Cursor
```

### 开发者发布新版本

```bash
# 1. 更新版本号
vim setup.py  # version="1.0.2"

# 2. 重新构建
python -m build

# 3. 发布
twine upload dist/*

# 4. 用户更新
pip install --upgrade mobile-mcp-ai
```

## 📋 发布检查清单

发布前检查：

- [ ] 版本号已更新
- [ ] CHANGELOG已更新
- [ ] README已更新
- [ ] 代码已测试
- [ ] 依赖已检查
- [ ] 构建成功
- [ ] TestPyPI测试通过
- [ ] 文档完整

## 🎉 发布后

发布成功后，其他人就可以：

1. **安装包**：`pip install mobile-mcp-ai`
2. **配置Cursor**：添加MCP配置
3. **开始使用**：在Cursor中直接用自然语言控制手机

**完全不需要了解代码细节！** 🚀

