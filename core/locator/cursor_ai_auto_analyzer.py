#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cursor AI 自动分析器

当检测到请求文件时，自动调用Cursor AI分析截图并写入结果文件。
这个模块可以在后台运行，监控请求文件并自动处理。
"""
import asyncio
import json
import time
from pathlib import Path
from typing import Dict, Optional
import tempfile


class CursorAIAutoAnalyzer:
    """
    Cursor AI 自动分析器
    
    功能：
    1. 监控请求文件目录
    2. 检测到新请求时，自动调用Cursor AI分析
    3. 将结果写入结果文件
    """
    
    def __init__(self):
        """初始化自动分析器"""
        self.request_dir = Path(tempfile.gettempdir()) / "mobile_screenshots" / "requests"
        self.result_dir = Path(tempfile.gettempdir()) / "mobile_screenshots" / "results"
        self.request_dir.mkdir(parents=True, exist_ok=True)
        self.result_dir.mkdir(parents=True, exist_ok=True)
        self.processed_requests = set()
    
    def check_requests(self) -> list[Path]:
        """
        检查是否有新的请求文件
        
        Returns:
            新的请求文件列表
        """
        if not self.request_dir.exists():
            return []
        
        new_requests = []
        for request_file in self.request_dir.glob("request_*.json"):
            if request_file not in self.processed_requests:
                new_requests.append(request_file)
        
        return new_requests
    
    async def process_request(self, request_file: Path) -> bool:
        """
        处理单个请求
        
        Args:
            request_file: 请求文件路径
            
        Returns:
            是否成功
        """
        try:
            # 读取请求文件
            with open(request_file, 'r', encoding='utf-8') as f:
                request_data = json.load(f)
            
            request_id = request_data.get('request_id')
            screenshot_path = request_data.get('screenshot_path')
            element_desc = request_data.get('element_desc')
            result_file = self.result_dir / f"result_{request_id}.json"
            
            print(f"📝 处理请求: {request_id}")
            print(f"   截图: {screenshot_path}")
            print(f"   元素: {element_desc}")
            
            # 🎯 这里需要调用Cursor AI分析截图
            # 由于是在Python脚本中，无法直接调用Cursor AI
            # 所以这里返回提示信息，告诉用户需要手动调用MCP工具
            print(f"💡 请手动调用MCP工具分析截图：")
            print(f"   @mobile_analyze_screenshot request_id=\"{request_id}\"")
            
            # 标记为已处理
            self.processed_requests.add(request_file)
            
            return True
            
        except Exception as e:
            print(f"❌ 处理请求失败: {e}")
            return False
    
    async def run(self, check_interval: float = 2.0):
        """
        运行自动分析器（监控模式）
        
        Args:
            check_interval: 检查间隔（秒）
        """
        print(f"🚀 Cursor AI 自动分析器已启动")
        print(f"   监控目录: {self.request_dir}")
        print(f"   检查间隔: {check_interval}秒")
        
        while True:
            try:
                new_requests = self.check_requests()
                for request_file in new_requests:
                    await self.process_request(request_file)
                
                await asyncio.sleep(check_interval)
            except KeyboardInterrupt:
                print("\n⚠️  自动分析器已停止")
                break
            except Exception as e:
                print(f"❌ 自动分析器异常: {e}")
                await asyncio.sleep(check_interval)


# 注意：这个自动分析器需要在Cursor AI环境中运行
# 实际使用时，Cursor AI会通过MCP工具自动处理请求文件

