#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
iOS客户端 - WDA版本（已重构，使用统一管理器）

功能：
1. iOS设备连接管理
2. 基础的WDA操作
3. 截图、点击、元素列表等功能已移至统一管理器
"""

import time
import re
from typing import Dict, Optional, List
from .ios_device_manager_wda import IOSDeviceManagerWDA


class IOSClientWDA:
    """iOS WDA客户端（重构版本）"""
    
    def __init__(self, device_id: Optional[str] = None, lazy_connect: bool = False):
        """
        初始化iOS客户端
        
        Args:
            device_id: 设备UDID，None则自动选择第一个设备
            lazy_connect: 是否延迟连接
        """
        self.device_id = device_id
        self._lazy_connect = lazy_connect
        
        # 设备管理器
        self.device_manager = IOSDeviceManagerWDA()
        
        # WDA客户端
        self.wda = None if lazy_connect else self._connect_wda()
        
        # 操作历史（兼容性）
        self.operation_history: List[Dict] = []
        
        # 缓存
        self._snapshot_cache = None
        self._cache_timestamp = 0
        self._cache_ttl = 1  # 缓存1秒
    
    def _connect_wda(self):
        """连接WDA服务"""
        try:
            import wda
            
            # 获取设备列表
            devices = self.device_manager.list_devices()
            if not devices:
                raise RuntimeError("未找到iOS设备")
            
            # 选择设备
            device_udid = self.device_id or devices[0]['udid']
            
            # 连接WDA
            wda_client = wda.Client(device_udid)
            
            # 测试连接
            status = wda_client.status()
            if not status:
                raise RuntimeError("WDA服务未启动")
            
            print(f"✅ iOS WDA连接成功: {device_udid}", file=sys.stderr)
            return wda_client
            
        except Exception as e:
            raise RuntimeError(f"连接WDA失败: {e}")
    
    def _ensure_connected(self):
        """确保WDA已连接"""
        if self.wda is None:
            if self._lazy_connect:
                self.wda = self._connect_wda()
            else:
                raise RuntimeError("WDA客户端未初始化")
    
    def get_page_source(self) -> str:
        """获取页面源码"""
        self._ensure_connected()
        
        try:
            # 检查缓存
            current_time = time.time()
            if self._snapshot_cache and (current_time - self._cache_timestamp < self._cache_ttl):
                return self._snapshot_cache
            
            # 获取源码
            source = self.wda.source()
            
            # 更新缓存
            self._snapshot_cache = source
            self._cache_timestamp = current_time
            
            return source
        except Exception as e:
            raise RuntimeError(f"获取页面源码失败: {e}")
    
    def get_screen_size(self) -> tuple:
        """获取屏幕尺寸"""
        self._ensure_connected()
        
        try:
            window = self.wda.window_size()
            return (window.width, window.height)
        except Exception as e:
            raise RuntimeError(f"获取屏幕尺寸失败: {e}")
    
    def press_key(self, key: str) -> Dict:
        """按键"""
        self._ensure_connected()
        
        try:
            if key == 'home':
                self.wda.press('home')
            elif key == 'back':
                # iOS没有返回键，可以用home代替
                self.wda.press('home')
            elif key == 'lock':
                self.wda.press('lock')
            else:
                return {"success": False, "message": f"❌ iOS不支持按键: {key}"}
            
            return {"success": True, "message": f"✅ 按键成功: {key}"}
        except Exception as e:
            return {"success": False, "message": f"❌ 按键失败: {e}"}
    
    def app_activate(self, bundle_id: str) -> Dict:
        """激活应用"""
        self._ensure_connected()
        
        try:
            self.wda.app_activate(bundle_id)
            return {"success": True, "message": f"✅ 应用激活成功: {bundle_id}"}
        except Exception as e:
            return {"success": False, "message": f"❌ 应用激活失败: {e}"}
    
    def app_terminate(self, bundle_id: str) -> Dict:
        """终止应用"""
        self._ensure_connected()
        
        try:
            self.wda.app_terminate(bundle_id)
            return {"success": True, "message": f"✅ 应用终止成功: {bundle_id}"}
        except Exception as e:
            return {"success": False, "message": f"❌ 应用终止失败: {e}"}
    
    def tap(self, x: int, y: int, duration: float = 0.1) -> None:
        """点击坐标"""
        self._ensure_connected()
        self.wda.tap(x, y, duration)
    
    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration: float = 0.5) -> None:
        """滑动"""
        self._ensure_connected()
        self.wda.swipe(x1, y1, x2, y2, duration)
    
    # ==================== 兼容性方法 ====================
    
    def list_elements(self) -> List[Dict]:
        """列出元素（兼容性方法，建议使用ElementManager）"""
        # 这里返回空列表，实际应该使用ElementManager
        return []
    
    def take_screenshot(self, filepath: str) -> None:
        """截图（兼容性方法，建议使用ScreenshotManager）"""
        self._ensure_connected()
        self.wda.screenshot(filepath)
    
    # ==================== 辅助方法 ====================
    
    def _parse_bounds_coords(self, bounds_str: str) -> tuple:
        """解析bounds字符串，返回中心点坐标"""
        try:
            match = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds_str)
            if match:
                x1, y1, x2, y2 = map(int, match.groups())
                return ((x1 + x2) // 2, (y1 + y2) // 2)
            return (0, 0)
        except:
            return (0, 0)
    
    def find_element(self, locator: str):
        """查找元素（增强版）"""
        self._ensure_connected()
        
        try:
            # 尝试多种定位方式
            element = None
            
            # 1. accessibility_id
            try:
                element = self.wda.find_element_by_accessibility_id(locator)
            except:
                pass
            
            # 2. name
            if not element:
                try:
                    element = self.wda.find_element_by_name(locator)
                except:
                    pass
            
            # 3. class name
            if not element:
                try:
                    element = self.wda.find_element_by_class_name(locator)
                except:
                    pass
            
            return element
            
        except Exception:
            return None
    
    def find_elements(self, locator: str) -> List:
        """查找多个元素"""
        self._ensure_connected()
        
        try:
            elements = []
            
            # 尝试多种定位方式
            try:
                elements = self.wda.find_elements_by_accessibility_id(locator)
            except:
                pass
            
            if not elements:
                try:
                    elements = self.wda.find_elements_by_name(locator)
                except:
                    pass
            
            if not elements:
                try:
                    elements = self.wda.find_elements_by_class_name(locator)
                except:
                    pass
            
            return elements
            
        except Exception:
            return []
    
    @property
    def active_element(self):
        """获取当前焦点元素"""
        self._ensure_connected()
        return self.wda.active_element
