# 包发布指南

## 📦 发布流程

### 1. 准备发布

```bash
# 确保代码已提交
git add .
git commit -m "准备发布 v1.0.0"
git tag v1.0.0
git push origin master --tags
```

### 2. 构建包

```bash
cd backend/mobile_mcp

# 安装构建工具
pip install build twine

# 构建包
python -m build
```

### 3. 发布到PyPI

```bash
# 测试发布（TestPyPI）
twine upload --repository testpypi dist/*

# 正式发布（PyPI）
twine upload dist/*
```

## 🔄 更新版本

### 修改代码后是否需要重新发布？

**答案：是的，需要重新发布**

### 原因：

1. **MCP Server是本地运行的**
   - Cursor配置的是本地Python脚本路径
   - 如果代码更新了，需要重新安装包或更新代码

2. **两种使用方式**：

#### 方式1: 直接使用本地代码（开发模式）

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

**优点**：
- 代码修改后立即生效
- 不需要重新发布

**缺点**：
- 需要手动配置路径
- 其他人使用不方便

#### 方式2: 使用pip安装的包（生产模式）

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

**优点**：
- 配置简单
- 统一版本管理

**缺点**：
- 代码修改后需要重新发布和安装

### 推荐方案：

**开发阶段**：使用方式1（本地代码）
**生产使用**：使用方式2（pip包）+ 版本管理

## 📝 版本管理

### 版本号规则（Semantic Versioning）

- **MAJOR.MINOR.PATCH**
  - MAJOR: 不兼容的API变更
  - MINOR: 向后兼容的功能新增
  - PATCH: 向后兼容的问题修复

### 更新版本号

```python
# setup.py
version="1.0.1"  # 修复bug
version="1.1.0"  # 新增功能
version="2.0.0"  # 重大变更
```

## 🔌 真机连接说明

### 在Cursor中配置MCP后，连接真机可以使用吗？

**答案：可以！**

### 工作原理：

1. **MCP Server运行在你的电脑上**
   - Cursor通过stdio与MCP Server通信
   - MCP Server通过ADB/WebDriverAgent连接真机

2. **连接流程**：

```
Cursor AI
  ↓ (stdio通信)
MCP Server (运行在你的电脑)
  ↓ (ADB/WebDriverAgent)
真机/模拟器
```

3. **配置示例**：

```json
{
  "mcpServers": {
    "mobile-automation": {
      "command": "python",
      "args": ["-m", "mobile_mcp.mcp.mcp_server"],
      "env": {
        "MOBILE_DEVICE_ID": "auto"  // 自动选择第一个设备
        // 或指定设备ID: "MOBILE_DEVICE_ID": "emulator-5554"
      }
    }
  }
}
```

4. **真机连接要求**：

**Android真机**：
- USB连接并启用USB调试
- 运行 `adb devices` 能看到设备
- 设备上已安装ATX（uiautomator2会自动安装）

**iOS真机**：
- USB连接
- 信任电脑
- 已安装WebDriverAgent
- 运行 `idevice_id -l` 能看到设备

5. **网络连接（可选）**：

如果真机通过WiFi连接（Android）：

```bash
# 在电脑上运行
adb tcpip 5555
adb connect <设备IP>:5555
```

然后在Cursor配置中：
```json
{
  "env": {
    "MOBILE_DEVICE_ID": "<设备IP>:5555"
  }
}
```

## 🎯 最佳实践

### 1. 开发阶段

```bash
# 使用本地代码，修改后立即生效
# Cursor配置使用绝对路径
```

### 2. 团队使用

```bash
# 发布到PyPI
pip install mobile-mcp-ai

# Cursor配置使用模块方式
# 统一版本，避免不一致
```

### 3. 版本更新

```bash
# 更新版本号
vim setup.py  # 修改version

# 重新构建和发布
python -m build
twine upload dist/*

# 用户更新
pip install --upgrade mobile-mcp-ai
```

## 📋 发布检查清单

- [ ] 更新版本号
- [ ] 更新CHANGELOG.md
- [ ] 运行测试确保通过
- [ ] 更新文档
- [ ] 构建包
- [ ] 测试安装
- [ ] 发布到PyPI
- [ ] 创建GitHub Release

## 🔗 相关资源

- [PyPI发布指南](https://packaging.python.org/tutorials/packaging-projects/)
- [Semantic Versioning](https://semver.org/)
- [MCP协议文档](https://modelcontextprotocol.io/)

