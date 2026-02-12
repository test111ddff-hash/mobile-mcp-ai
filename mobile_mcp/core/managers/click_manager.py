#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一点击管理器 - 合并所有点击功能

功能：
1. 统一点击接口
2. 支持text、id、coords、percent、som等所有点击方式
3. 自动平台检测和适配
"""

import asyncio
import re
from typing import Dict, Optional


class ClickManager:
    """统一点击管理器"""
    
    def __init__(self, mobile_client):
        self.client = mobile_client
    
    def _is_ios(self) -> bool:
        """判断当前是否为 iOS 平台"""
        return getattr(self.client, 'platform', 'android') == 'ios'
    
    def _get_ios_client(self):
        """获取 iOS 客户端"""
        if hasattr(self.client, '_ios_client') and self.client._ios_client:
            return self.client._ios_client
        if hasattr(self.client, 'wda') and self.client.wda:
            return self.client.wda
        return None
    
    def click(self, method: str, **kwargs) -> Dict:
        """统一点击接口
        
        Args:
            method: 点击方式 'text'|'id'|'coords'|'percent'|'som'
            **kwargs: 各种点击方式的参数
        
        Returns:
            操作结果
        """
        if method == 'text':
            return self.click_by_text(kwargs.get('text'), 
                                    position=kwargs.get('position'),
                                    verify=kwargs.get('verify'))
        elif method == 'id':
            return self.click_by_id(kwargs.get('resource_id'),
                                  index=kwargs.get('index', 0))
        elif method == 'coords':
            return self.click_at_coords(kwargs.get('x'), kwargs.get('y'),
                                       image_width=kwargs.get('image_width', 0),
                                       image_height=kwargs.get('image_height', 0),
                                       crop_offset_x=kwargs.get('crop_offset_x', 0),
                                       crop_offset_y=kwargs.get('crop_offset_y', 0),
                                       original_img_width=kwargs.get('original_img_width', 0),
                                       original_img_height=kwargs.get('original_img_height', 0))
        elif method == 'percent':
            return self.click_by_percent(kwargs.get('x_percent'), kwargs.get('y_percent'))
        elif method == 'som':
            return self.click_by_som(kwargs.get('index'))
        else:
            return {"success": False, "message": f"❌ 不支持的点击方式: {method}"}
    
    def click_by_text(self, text: str, timeout: float = 3.0, position: Optional[str] = None, 
                       verify: Optional[str] = None) -> Dict:
        """通过文本点击 - 统一实现"""
        try:
            if self._is_ios():
                return self._click_by_text_ios(text, timeout, position, verify)
            else:
                return self._click_by_text_android(text, timeout, position, verify)
        except Exception as e:
            return {"success": False, "message": f"❌ 文本点击失败: {e}"}
    
    def _click_by_text_android(self, text: str, timeout: float, position: Optional[str], verify: Optional[str]) -> Dict:
        """Android文本点击实现"""
        try:
            # 1. 获取页面XML
            xml_string = self.client.u2.dump_hierarchy(compressed=False)
            
            # 2. 查找匹配的元素
            matching_elements = []
            
            # 精确匹配
            for elem in self._find_elements_by_text(xml_string, text, exact=True):
                matching_elements.append(elem)
            
            # 如果精确匹配没有结果，尝试模糊匹配
            if not matching_elements:
                for elem in self._find_elements_by_text(xml_string, text, exact=False):
                    matching_elements.append(elem)
            
            if not matching_elements:
                return {"success": False, "message": f"❌ 未找到文本: {text}"}
            
            # 3. 处理位置参数
            target_element = None
            if position and len(matching_elements) > 1:
                # 根据位置选择元素
                if position == 'top':
                    target_element = min(matching_elements, key=lambda e: e['y1'])
                elif position == 'bottom':
                    target_element = max(matching_elements, key=lambda e: e['y1'])
                elif position == 'left':
                    target_element = min(matching_elements, key=lambda e: e['x1'])
                elif position == 'right':
                    target_element = max(matching_elements, key=lambda e: e['x1'])
                else:
                    target_element = matching_elements[0]
            else:
                target_element = matching_elements[0]
            
            # 4. 点击元素
            x = (target_element['x1'] + target_element['x2']) // 2
            y = (target_element['y1'] + target_element['y2']) // 2
            
            self.client.u2.click(x, y)
            
            # 5. 验证（如果指定了verify）
            if verify:
                # 等待页面变化
                asyncio.sleep(0.5)
                if self._check_text_exists(verify):
                    return {"success": True, "message": f"✅ 点击成功并验证到文本: {verify}"}
                else:
                    return {"success": True, "message": f"⚠️ 点击成功但未验证到期望文本: {verify}"}
            
            return {"success": True, "message": f"✅ 点击文本成功: {text}"}
            
        except Exception as e:
            return {"success": False, "message": f"❌ Android文本点击失败: {e}"}
    
    def _click_by_text_ios(self, text: str, timeout: float, position: Optional[str], verify: Optional[str]) -> Dict:
        """iOS文本点击实现"""
        try:
            ios_client = self._get_ios_client()
            if not ios_client:
                return {"success": False, "message": "❌ iOS客户端未初始化"}
            
            # iOS使用WDA的文本查找
            elements = ios_client.wda.find_elements_by_name(text)
            
            if not elements:
                return {"success": False, "message": f"❌ 未找到文本: {text}"}
            
            # 处理位置参数
            target_element = None
            if position and len(elements) > 1:
                # 根据位置选择元素（简化实现）
                if position == 'top':
                    target_element = elements[0]
                elif position == 'bottom':
                    target_element = elements[-1]
                else:
                    target_element = elements[0]
            else:
                target_element = elements[0]
            
            # 点击元素
            target_element.click()
            
            # 验证
            if verify:
                asyncio.sleep(0.5)
                verify_elements = ios_client.wda.find_elements_by_name(verify)
                if verify_elements:
                    return {"success": True, "message": f"✅ 点击成功并验证到文本: {verify}"}
                else:
                    return {"success": True, "message": f"⚠️ 点击成功但未验证到期望文本: {verify}"}
            
            return {"success": True, "message": f"✅ 点击文本成功: {text}"}
            
        except Exception as e:
            return {"success": False, "message": f"❌ iOS文本点击失败: {e}"}
    
    def click_by_id(self, resource_id: str, index: int = 0) -> Dict:
        """通过resource-id点击 - 统一实现"""
        try:
            if self._is_ios():
                return self._click_by_id_ios(resource_id, index)
            else:
                return self._click_by_id_android(resource_id, index)
        except Exception as e:
            return {"success": False, "message": f"❌ ID点击失败: {e}"}
    
    def _click_by_id_android(self, resource_id: str, index: int) -> Dict:
        """Android ID点击实现"""
        try:
            # 标准化resource-id
            normalized_id = self._normalize_resource_id(resource_id)
            
            # 查找元素
            elements = self.client.u2(resourceId=normalized_id)
            if not elements.exists(timeout=2):
                return {"success": False, "message": f"❌ 未找到resource-id: {normalized_id}"}
            
            # 如果有多个元素，选择指定索引
            all_elements = elements.all()
            if index >= len(all_elements):
                return {"success": False, "message": f"❌ 索引超出范围: {index} >= {len(all_elements)}"}
            
            target_element = all_elements[index]
            target_element.click()
            
            return {"success": True, "message": f"✅ ID点击成功: {normalized_id}[{index}]"}
            
        except Exception as e:
            return {"success": False, "message": f"❌ Android ID点击失败: {e}"}
    
    def _click_by_id_ios(self, resource_id: str, index: int) -> Dict:
        """iOS ID点击实现"""
        try:
            ios_client = self._get_ios_client()
            if not ios_client:
                return {"success": False, "message": "❌ iOS客户端未初始化"}
            
            # iOS使用不同的属性名
            elements = []
            try:
                # 尝试多种定位方式
                elements = ios_client.wda.find_elements_by_accessibility_id(resource_id)
                if not elements:
                    elements = ios_client.wda.find_elements_by_name(resource_id)
                if not elements:
                    elements = ios_client.wda.find_elements_by_class_name(resource_id)
            except:
                pass
            
            if not elements:
                return {"success": False, "message": f"❌ 未找到元素: {resource_id}"}
            
            if index >= len(elements):
                return {"success": False, "message": f"❌ 索引超出范围: {index} >= {len(elements)}"}
            
            target_element = elements[index]
            target_element.click()
            
            return {"success": True, "message": f"✅ iOS元素点击成功: {resource_id}[{index}]"}
            
        except Exception as e:
            return {"success": False, "message": f"❌ iOS ID点击失败: {e}"}
    
    def click_at_coords(self, x: int, y: int, image_width: int = 0, image_height: int = 0,
                        crop_offset_x: int = 0, crop_offset_y: int = 0,
                        original_img_width: int = 0, original_img_height: int = 0) -> Dict:
        """点击坐标 - 统一实现"""
        try:
            # 坐标转换（如果需要）
            final_x, final_y = self._convert_coordinates(x, y, image_width, image_height,
                                                        crop_offset_x, crop_offset_y,
                                                        original_img_width, original_img_height)
            
            if self._is_ios():
                ios_client = self._get_ios_client()
                if not ios_client:
                    return {"success": False, "message": "❌ iOS客户端未初始化"}
                ios_client.wda.tap(final_x, final_y)
            else:
                self.client.u2.click(final_x, final_y)
            
            return {"success": True, "message": f"✅ 坐标点击成功: ({final_x}, {final_y})"}
            
        except Exception as e:
            return {"success": False, "message": f"❌ 坐标点击失败: {e}"}
    
    def click_by_percent(self, x_percent: float, y_percent: float) -> Dict:
        """通过百分比坐标点击 - 统一实现"""
        try:
            # 获取屏幕尺寸
            if self._is_ios():
                ios_client = self._get_ios_client()
                if not ios_client:
                    return {"success": False, "message": "❌ iOS客户端未初始化"}
                size = ios_client.wda.window_size()
                screen_width, screen_height = size.width, size.height
            else:
                info = self.client.u2.info
                screen_width = info.get('displayWidth', 720)
                screen_height = info.get('displayHeight', 1280)
            
            # 计算实际坐标
            x = int(screen_width * x_percent / 100)
            y = int(screen_height * y_percent / 100)
            
            # 点击
            if self._is_ios():
                ios_client.wda.tap(x, y)
            else:
                self.client.u2.click(x, y)
            
            return {"success": True, "message": f"✅ 百分比点击成功: ({x_percent}%, {y_percent}%) -> ({x}, {y})"}
            
        except Exception as e:
            return {"success": False, "message": f"❌ 百分比点击失败: {e}"}
    
    def click_by_som(self, index: int) -> Dict:
        """根据SoM编号点击 - 统一实现"""
        try:
            # 这里需要配合SOM截图的元素信息
            # 简化实现，实际应该从之前的SOM截图结果中获取元素坐标
            if not hasattr(self, '_som_elements'):
                return {"success": False, "message": "❌ 请先调用take_screenshot_with_som获取元素信息"}
            
            if index < 1 or index > len(self._som_elements):
                return {"success": False, "message": f"❌ SoM编号超出范围: {index}"}
            
            element = self._som_elements[index - 1]
            x = (element['x1'] + element['x2']) // 2
            y = (element['y1'] + element['y2']) // 2
            
            if self._is_ios():
                ios_client = self._get_ios_client()
                ios_client.wda.tap(x, y)
            else:
                self.client.u2.click(x, y)
            
            return {"success": True, "message": f"✅ SoM点击成功: #{index}"}
            
        except Exception as e:
            return {"success": False, "message": f"❌ SoM点击失败: {e}"}
    
    def _find_elements_by_text(self, xml_string: str, text: str, exact: bool = True) -> list:
        """从XML中查找包含指定文本的元素"""
        elements = []
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(xml_string)
            
            def search_node(node):
                elem_text = node.get('text', '')
                desc = node.get('content-desc', '')
                
                found = False
                if exact:
                    if elem_text == text or desc == text:
                        found = True
                else:
                    if text in elem_text or text in desc:
                        found = True
                
                if found:
                    bounds_str = node.get('bounds', '')
                    if bounds_str:
                        match = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds_str)
                        if match:
                            x1, y1, x2, y2 = map(int, match.groups())
                            elements.append({
                                'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
                                'text': elem_text,
                                'desc': desc
                            })
                
                # 递归搜索子节点
                for child in node:
                    search_node(child)
            
            search_node(root)
        except Exception:
            pass
        
        return elements
    
    def _normalize_resource_id(self, resource_id: str) -> str:
        """标准化resource-id"""
        # 如果已经是完整ID，直接返回
        if ":" in resource_id or "/" in resource_id:
            return resource_id
        
        # 尝试获取当前包名
        try:
            if not self._is_ios():
                current_package = self.client.u2.app_current().get('package')
                if current_package:
                    return f"{current_package}:id/{resource_id}"
        except:
            pass
        
        return resource_id
    
    def _convert_coordinates(self, x: int, y: int, image_width: int, image_height: int,
                           crop_offset_x: int, crop_offset_y: int,
                           original_img_width: int, original_img_height: int) -> tuple:
        """坐标转换（处理压缩截图的坐标换算）"""
        # 如果没有原始尺寸信息，直接返回原坐标
        if original_img_width == 0 or original_img_height == 0:
            return x, y
        
        # 如果有裁剪偏移，需要加上偏移量
        if crop_offset_x > 0 or crop_offset_y > 0:
            x += crop_offset_x
            y += crop_offset_y
        
        # 如果图片被压缩了，需要按比例缩放坐标
        if image_width != original_img_width or image_height != original_img_height:
            scale_x = original_img_width / image_width
            scale_y = original_img_height / image_height
            x = int(x * scale_x)
            y = int(y * scale_y)
        
        return x, y
    
    def _check_text_exists(self, text: str) -> bool:
        """检查文本是否存在"""
        try:
            if self._is_ios():
                ios_client = self._get_ios_client()
                elements = ios_client.wda.find_elements_by_name(text)
                return len(elements) > 0
            else:
                elem = self.client.u2(text=text)
                return elem.exists(timeout=1)
        except:
            return False
    
    def set_som_elements(self, elements: list):
        """设置SoM元素信息（供click_by_som使用）"""
        self._som_elements = elements
