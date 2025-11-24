# Cursor配置名称建议

## 🎯 命名对比

### 开源项目
- **包名**: `mobile-mcp` (npm)
- **特点**: 基础功能

### 你的项目
- **包名**: `mobile-mcp-ai` (PyPI)
- **特点**: AI增强，智能定位

## 💡 推荐方案

### ⭐ 方案1: `mobile-mcp-ai`（最推荐）

**优点**：
- ✅ 和包名完全一致
- ✅ 清晰表明是增强版
- ✅ 用户容易记住和配置
- ✅ 和开源项目有明显区别

**配置示例**：
```json
{
  "mcpServers": {
    "mobile-mcp-ai": {
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

### 方案2: `mobile-ai-automation`

**优点**：
- ✅ 强调AI能力
- ✅ 有特色，容易识别

**配置示例**：
```json
{
  "mcpServers": {
    "mobile-ai-automation": {
      "command": "python",
      "args": ["-m", "mobile_mcp.mcp.mcp_server"],
      "env": {
        "MOBILE_DEVICE_ID": "auto"
      }
    }
  }
}
```

### 方案3: `mobile-smart-automation`

**优点**：
- ✅ 强调智能定位
- ✅ 突出核心能力

**配置示例**：
```json
{
  "mcpServers": {
    "mobile-smart-automation": {
      "command": "python",
      "args": ["-m", "mobile_mcp.mcp.mcp_server"],
      "env": {
        "MOBILE_DEVICE_ID": "auto"
      }
    }
  }
}
```

## 🎨 我的推荐

**强烈推荐使用 `mobile-mcp-ai`**：

1. **一致性**：和包名一致，用户不会混淆
2. **清晰性**：`-enhanced` 后缀明确表示增强版
3. **区别性**：和开源项目 `mobile-mcp` 有明显区别
4. **专业性**：符合Python包命名规范

## 📝 需要更新的地方

如果选择 `mobile-mcp-ai`，需要更新：

1. **mcp_server.py**：
   ```python
   server = Server("mobile-mcp-ai")  # 已更新 ✅
   ```

2. **文档**：所有文档中的配置示例

## ✅ 最终配置

```json
{
  "mcpServers": {
    "mobile-mcp-ai": {
      "command": "python",
      "args": ["-m", "mobile_mcp.mcp.mcp_server"],
      "env": {
        "MOBILE_DEVICE_ID": "auto",
        "AI_ENHANCEMENT_ENABLED": "true",
        "DEFAULT_PLATFORM": "android"
      }
    }
  }
}
```

