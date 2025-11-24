#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mobile MCP HTTP Server - 局域网共享版本

功能：
1. 启动HTTP服务器，提供MCP工具访问
2. 支持局域网内其他用户通过HTTP连接
3. 使用REST API提供移动端自动化能力
4. 支持标准 MCP SSE 协议，可直接在 Cursor 中配置

启动方式：
    python mcp_http_server.py --host 0.0.0.0 --port 8080

其他人配置（Cursor mcp.json）：
    {
      "mcpServers": {
        "mobile-automation": {
          "url": "http://YOUR_IP:8080/mcp"
        }
      }
    }
"""
import asyncio
import sys
import json
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime

# 添加项目路径
mobile_mcp_dir = Path(__file__).parent.parent
project_root = mobile_mcp_dir.parent.parent
backend_dir = project_root / "backend"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_dir))

try:
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.responses import JSONResponse, StreamingResponse
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    print("⚠️  FastAPI未安装，请运行: pip install fastapi uvicorn", file=sys.stderr)

from mobile_mcp.mcp.mcp_server import MobileMCPServer


class MobileMCPHTTPServer:
    """Mobile MCP HTTP服务器"""
    
    def __init__(self):
        """初始化HTTP服务器"""
        self.mcp_server = MobileMCPServer()
        self.app = FastAPI(title="Mobile MCP HTTP Server", version="1.0.0")
        
        # 配置CORS（允许跨域访问）
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # 生产环境应该限制域名
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # 注册路由
        self._register_routes()
    
    def _register_routes(self):
        """注册API路由"""
        
        @self.app.get("/")
        async def root():
            """根路径，返回服务信息"""
            return {
                "service": "Mobile MCP HTTP Server",
                "version": "1.0.0",
                "status": "running",
                "endpoints": {
                    "mcp": "/mcp (MCP SSE Protocol - for Cursor)",
                    "tools": "/api/tools",
                    "call_tool": "/api/call_tool",
                    "health": "/api/health"
                }
            }
        
        @self.app.post("/mcp")
        @self.app.get("/mcp")
        async def mcp_endpoint(request: Request):
            """
            标准 MCP 端点 - 支持 JSON-RPC 2.0 协议
            这个端点可以让 Cursor 直接连接 MCP 服务器
            """
            try:
                # 如果是 GET 请求，返回 SSE 连接（但当前实现为简单 POST）
                if request.method == "GET":
                    return JSONResponse({
                        "jsonrpc": "2.0",
                        "result": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {
                                "tools": {}
                            },
                            "serverInfo": {
                                "name": "mobile-automation",
                                "version": "1.0.0"
                            }
                        }
                    })
                
                # POST 请求：处理 JSON-RPC 消息
                body = await request.json()
                
                # JSON-RPC 2.0 格式
                jsonrpc = body.get("jsonrpc", "2.0")
                method = body.get("method")
                params = body.get("params", {})
                request_id = body.get("id")
                
                # 🎯 智能 ADB 连接：尝试连接客户端的 ADB 服务器
                # 1. 优先使用请求头指定的 ADB 服务器
                adb_server = request.headers.get("X-ADB-Server")
                
                # 2. 如果没有指定，尝试使用客户端的 IP 地址
                if not adb_server:
                    client_ip = request.client.host
                    # 排除本地连接，只对远程客户端尝试
                    if client_ip and client_ip not in ["127.0.0.1", "localhost", "::1"]:
                        adb_server = client_ip
                
                # 3. 如果检测到远程客户端，设置 ADB 连接
                if adb_server:
                    import os
                    adb_socket = f"tcp:{adb_server}:5037"
                    
                    # 每次都设置，确保能连接到远程ADB（即使之前初始化失败）
                    current_socket = os.environ.get("ADB_SERVER_SOCKET")
                    if current_socket != adb_socket:
                        os.environ["ADB_SERVER_SOCKET"] = adb_socket
                        print(f"🌐 自动检测到客户端 ADB: {adb_server}:5037", file=sys.stderr)
                        # 如果已经初始化过但ADB地址变了，需要重新初始化
                        if self.mcp_server._initialized:
                            print(f"🔄 ADB地址变更，重新初始化...", file=sys.stderr)
                            self.mcp_server._initialized = False
                
                # 确保MCP Server已初始化
                await self.mcp_server.initialize()
                
                # 路由到不同的方法
                if method == "initialize":
                    # 初始化连接
                    result = {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": {
                            "name": "mobile-automation",
                            "version": "1.0.0"
                        }
                    }
                    return JSONResponse({
                        "jsonrpc": jsonrpc,
                        "result": result,
                        "id": request_id
                    })
                
                elif method == "tools/list":
                    # 列出工具
                    tools = self.mcp_server.get_tools()
                    result = {
                        "tools": [
                            {
                                "name": tool.name,
                                "description": tool.description,
                                "inputSchema": tool.inputSchema
                            }
                            for tool in tools
                        ]
                    }
                    return JSONResponse({
                        "jsonrpc": jsonrpc,
                        "result": result,
                        "id": request_id
                    })
                
                elif method == "tools/call":
                    # 调用工具
                    tool_name = params.get("name")
                    arguments = params.get("arguments", {})
                    
                    if not tool_name:
                        return JSONResponse({
                            "jsonrpc": jsonrpc,
                            "error": {
                                "code": -32602,
                                "message": "Invalid params: missing tool name"
                            },
                            "id": request_id
                        })
                    
                    # 调用MCP Server的工具
                    result = await self.mcp_server.handle_tool_call(tool_name, arguments)
                    
                    # 转换为 JSON-RPC 响应格式
                    if result and len(result) > 0:
                        content = result[0].text
                        return JSONResponse({
                            "jsonrpc": jsonrpc,
                            "result": {
                                "content": [
                                    {
                                        "type": "text",
                                        "text": content
                                    }
                                ]
                            },
                            "id": request_id
                        })
                    else:
                        return JSONResponse({
                            "jsonrpc": jsonrpc,
                            "error": {
                                "code": -32603,
                                "message": "Tool call returned empty result"
                            },
                            "id": request_id
                        })
                
                else:
                    # 未知方法
                    return JSONResponse({
                        "jsonrpc": jsonrpc,
                        "error": {
                            "code": -32601,
                            "message": f"Method not found: {method}"
                        },
                        "id": request_id
                    })
                    
            except json.JSONDecodeError:
                return JSONResponse(
                    status_code=400,
                    content={
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32700,
                            "message": "Parse error"
                        },
                        "id": None
                    }
                )
            except Exception as e:
                import traceback
                traceback.print_exc()
                return JSONResponse(
                    status_code=500,
                    content={
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32603,
                            "message": f"Internal error: {str(e)}"
                        },
                        "id": body.get("id") if 'body' in locals() else None
                    }
                )
        
        @self.app.get("/api/health")
        async def health():
            """健康检查"""
            return {"status": "ok", "timestamp": datetime.now().isoformat()}
        
        @self.app.get("/api/tools")
        async def list_tools():
            """列出所有可用的工具"""
            try:
                tools = self.mcp_server.get_tools()
                return {
                    "success": True,
                    "tools": [
                        {
                            "name": tool.name,
                            "description": tool.description,
                            "inputSchema": tool.inputSchema
                        }
                        for tool in tools
                    ]
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/call_tool")
        async def call_tool(request: Request):
            """调用MCP工具"""
            try:
                body = await request.json()
                tool_name = body.get("name")
                arguments = body.get("arguments", {})
                
                if not tool_name:
                    raise HTTPException(status_code=400, detail="缺少工具名称")
                
                # 🎯 确保MCP Server已初始化
                await self.mcp_server.initialize()
                
                # 调用MCP Server的工具处理函数
                result = await self.mcp_server.handle_tool_call(tool_name, arguments)
                
                # 解析TextContent结果
                if result and len(result) > 0:
                    content = result[0].text
                    try:
                        # 尝试解析JSON
                        data = json.loads(content)
                        return JSONResponse(content=data)
                    except json.JSONDecodeError:
                        # 如果不是JSON，返回文本
                        return JSONResponse(content={"success": True, "message": content})
                else:
                    return JSONResponse(content={"success": False, "error": "工具调用返回空结果"})
                    
            except HTTPException:
                raise
            except Exception as e:
                import traceback
                traceback.print_exc()
                return JSONResponse(
                    status_code=500,
                    content={"success": False, "error": str(e)}
                )
        
        @self.app.get("/api/info")
        async def info():
            """获取服务器信息"""
            return {
                "server": "Mobile MCP HTTP Server",
                "version": "1.0.0",
                "mcp_tools": [
                    "mobile_click",
                    "mobile_input",
                    "mobile_swipe",
                    "mobile_snapshot",
                    "mobile_launch_app",
                    "mobile_assert_text",
                    "mobile_get_current_package",
                    "mobile_take_screenshot",
                    "mobile_analyze_screenshot"
                ]
            }


def main():
    """启动HTTP服务器"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Mobile MCP HTTP Server")
    parser.add_argument("--host", default="0.0.0.0", help="服务器地址（默认：0.0.0.0，允许局域网访问）")
    parser.add_argument("--port", type=int, default=8080, help="服务器端口（默认：8080）")
    parser.add_argument("--reload", action="store_true", help="开发模式：自动重载")
    
    args = parser.parse_args()
    
    if not FASTAPI_AVAILABLE:
        print("❌ FastAPI未安装，请运行: pip install fastapi uvicorn", file=sys.stderr)
        sys.exit(1)
    
    server = MobileMCPHTTPServer()
    
    # 获取本机IP地址
    local_ip = None
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        pass
    
    print("=" * 60, file=sys.stderr)
    print("🚀 Mobile MCP HTTP Server", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print(f"📡 服务器地址: http://{args.host}:{args.port}", file=sys.stderr)
    if local_ip:
        print(f"🌐 局域网访问: http://{local_ip}:{args.port}", file=sys.stderr)
    else:
        print(f"🌐 局域网访问: http://<你的IP>:{args.port}", file=sys.stderr)
    print(f"📋 API文档: http://{args.host}:{args.port}/docs", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print()
    print("💡 其他人使用步骤：", file=sys.stderr)
    print()
    print("1️⃣ 在有 Android 设备的电脑上运行:", file=sys.stderr)
    print("   ./enable_remote_adb.sh", file=sys.stderr)
    print()
    print("2️⃣ 在 Cursor 中配置:", file=sys.stderr)
    if local_ip:
        print(f'   "url": "http://{local_ip}:{args.port}/mcp"', file=sys.stderr)
    else:
        print(f'   "url": "http://<服务器IP>:{args.port}/mcp"', file=sys.stderr)
    print()
    print("3️⃣ 服务器会自动检测并连接客户端的 ADB 设备！", file=sys.stderr)
    print()
    
    # 启动服务器
    uvicorn.run(
        server.app,
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info"
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️  HTTP Server 已停止", file=sys.stderr)
    except Exception as e:
        print(f"❌ HTTP Server 错误: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()

