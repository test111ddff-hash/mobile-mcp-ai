#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
iOS客户端 - 类似Android的MobileClient

功能：
1. 设备连接管理
2. 页面结构获取（snapshot）
3. 元素操作（click, type, swipe等）
4. App管理（launch, stop等）

用法:
    client = IOSClient(device_id=None)
    await client.launch_app("com.example.app")
    await client.click("登录按钮")
"""
import asyncio
from typing import Dict, Optional, List

from .ios_device_manager import IOSDeviceManager


class IOSClient:
    """
    iOS客户端 - 类似Android的MobileClient
    
    用法:
        client = IOSClient(device_id=None)
        await client.launch_app("com.example.app")
        await client.click("登录按钮")
    """
    
    def __init__(self, device_id: Optional[str] = None):
        """
        初始化iOS客户端
        
        Args:
            device_id: 设备ID，None则自动选择第一个设备
        """
        self.device_manager = IOSDeviceManager()
        self.driver = self.device_manager.connect(device_id)
        
        # 操作历史（用于录制）
        self.operation_history: List[Dict] = []
    
    async def snapshot(self) -> str:
        """
        获取页面XML结构（类似Android的snapshot）
        
        Returns:
            格式化后的页面结构字符串
        """
        try:
            # 获取页面源码
            source = self.driver.page_source
            
            # 简单的格式化（可以后续优化）
            return source
        except Exception as e:
            raise RuntimeError(f"获取页面结构失败: {e}")
    
    async def click(self, element_desc: str, ref: Optional[str] = None):
        """
        点击元素
        
        Args:
            element_desc: 元素描述（自然语言）
            ref: 元素定位器（XPath、accessibility_id等）
            
        Returns:
            操作结果
        """
        try:
            from selenium.webdriver.common.by import By
            
            # 如果提供了ref，直接使用
            if ref:
                if ref.startswith('//') or ref.startswith('/'):
                    # XPath
                    element = self.driver.find_element(By.XPATH, ref)
                elif ref.startswith('id='):
                    # accessibility_id
                    element = self.driver.find_element(By.ID, ref.replace('id=', ''))
                else:
                    # 默认作为accessibility_id
                    element = self.driver.find_element(By.ID, ref)
            else:
                # 尝试多种定位方式
                selectors = [
                    (By.XPATH, f"//*[@name='{element_desc}']"),
                    (By.XPATH, f"//*[@label='{element_desc}']"),
                    (By.XPATH, f"//*[contains(@name, '{element_desc}')]"),
                ]
                
                element = None
                for by, selector in selectors:
                    try:
                        element = self.driver.find_element(by, selector)
                        break
                    except:
                        continue
                
                if not element:
                    raise ValueError(f"未找到元素: {element_desc}")
            
            element.click()
            
            # 记录操作
            self.operation_history.append({
                'action': 'click',
                'element': element_desc,
                'ref': ref or 'auto',
                'success': True
            })
            
            return {"success": True}
            
        except Exception as e:
            return {"success": False, "reason": str(e)}
    
    async def type_text(self, element_desc: str, text: str, ref: Optional[str] = None):
        """
        输入文本
        
        Args:
            element_desc: 元素描述
            text: 要输入的文本
            ref: 元素定位器
            
        Returns:
            操作结果
        """
        try:
            from selenium.webdriver.common.by import By
            
            # 定位输入框
            if ref:
                if ref.startswith('//'):
                    element = self.driver.find_element(By.XPATH, ref)
                else:
                    element = self.driver.find_element(By.ID, ref)
            else:
                # 查找第一个输入框
                element = self.driver.find_element(By.XPATH, "//XCUIElementTypeTextField | //XCUIElementTypeSecureTextField")
            
            element.clear()
            element.send_keys(text)
            
            # 记录操作
            self.operation_history.append({
                'action': 'type',
                'element': element_desc,
                'text': text,
                'ref': ref or 'auto',
                'success': True
            })
            
            return {"success": True}
            
        except Exception as e:
            return {"success": False, "reason": str(e)}
    
    async def swipe(self, direction: str):
        """
        滑动操作
        
        Args:
            direction: 滑动方向 ('up', 'down', 'left', 'right')
            
        Returns:
            操作结果
        """
        try:
            size = self.driver.get_window_size()
            width = size['width']
            height = size['height']
            
            if direction == 'up':
                self.driver.swipe(width // 2, int(height * 0.8), width // 2, int(height * 0.2))
            elif direction == 'down':
                self.driver.swipe(width // 2, int(height * 0.2), width // 2, int(height * 0.8))
            elif direction == 'left':
                self.driver.swipe(int(width * 0.8), height // 2, int(width * 0.2), height // 2)
            elif direction == 'right':
                self.driver.swipe(int(width * 0.2), height // 2, int(width * 0.8), height // 2)
            else:
                return {"success": False, "reason": f"不支持的滑动方向: {direction}"}
            
            return {"success": True}
            
        except Exception as e:
            return {"success": False, "reason": str(e)}
    
    async def launch_app(self, bundle_id: str, wait_time: int = 3):
        """
        启动应用
        
        Args:
            bundle_id: 应用Bundle ID，如 'com.example.app'
            wait_time: 等待时间（秒）
            
        Returns:
            操作结果
        """
        try:
            self.driver.activate_app(bundle_id)
            await asyncio.sleep(wait_time)
            
            return {"success": True}
        except Exception as e:
            return {"success": False, "reason": str(e)}
    
    def get_current_package(self) -> Optional[str]:
        """获取当前前台应用的Bundle ID"""
        try:
            return self.driver.current_package
        except:
            return None

