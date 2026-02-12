#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一元素管理器 - 合并元素列表功能

功能：
1. 统一元素列表接口
2. 自动平台检测和适配
3. 智能过滤和排序
"""

import xml.etree.ElementTree as ET
import re
from typing import List, Dict, Optional


class ElementManager:
    """统一元素管理器"""
    
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
    
    def list_elements(self, max_elements: int = 100, filter_interactive: bool = True) -> List[Dict]:
        """统一元素列表接口
        
        Args:
            max_elements: 最大返回元素数量
            filter_interactive: 是否只返回可交互元素
        
        Returns:
            元素列表
        """
        try:
            if self._is_ios():
                return self._list_elements_ios(max_elements, filter_interactive)
            else:
                return self._list_elements_android(max_elements, filter_interactive)
        except Exception as e:
            return [{"error": f"❌ 获取元素列表失败: {e}"}]
    
    def _list_elements_android(self, max_elements: int, filter_interactive: bool) -> List[Dict]:
        """Android元素列表实现"""
        try:
            # 获取XML
            xml_string = self.client.u2.dump_hierarchy(compressed=False)
            if not xml_string:
                return []
            
            root = ET.fromstring(xml_string)
            elements = []
            
            def parse_node(node, depth=0):
                if depth > 20 or len(elements) >= max_elements:  # 限制深度和数量
                    return
                
                # 提取属性
                text = node.get('text', '').strip()
                resource_id = node.get('resource-id', '')
                class_name = node.get('class', '')
                content_desc = node.get('content-desc', '').strip()
                bounds_str = node.get('bounds', '')
                clickable = node.get('clickable', 'false') == 'true'
                focusable = node.get('focusable', 'false') == 'true'
                enabled = node.get('enabled', 'true') == 'true'
                
                # 过滤条件
                if filter_interactive:
                    # 只保留可交互或有意义的元素
                    if not (clickable or focusable or text or resource_id or content_desc):
                        # 递归处理子节点
                        for child in node:
                            parse_node(child, depth + 1)
                        return
                
                # 解析bounds
                x, y, width, height = 0, 0, 0, 0
                if bounds_str:
                    match = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds_str)
                    if match:
                        x1, y1, x2, y2 = map(int, match.groups())
                        x, y = x1, y1
                        width, height = x2 - x1, y2 - y1
                
                # 简化类名
                class_name_simple = class_name.split('.')[-1] if class_name else ''
                
                # 构建元素信息
                element = {
                    'text': text,
                    'resource-id': resource_id,
                    'class': class_name_simple,
                    'content-desc': content_desc,
                    'bounds': bounds_str,
                    'x': x,
                    'y': y,
                    'width': width,
                    'height': height,
                    'clickable': clickable,
                    'focusable': focusable,
                    'enabled': enabled,
                    'depth': depth
                }
                
                elements.append(element)
                
                # 递归处理子节点
                for child in node:
                    parse_node(child, depth + 1)
            
            parse_node(root)
            
            # 智能排序：可交互元素优先，然后是有文本的元素
            elements.sort(key=lambda e: (
                not e.get('clickable', False),  # clickable优先
                not e.get('focusable', False),  # focusable次之
                not bool(e.get('text', '')),   # 有文本的优先
                e.get('depth', 0)               # 深度小的优先
            ))
            
            return elements[:max_elements]
            
        except Exception as e:
            return [{"error": f"❌ Android元素解析失败: {e}"}]
    
    def _list_elements_ios(self, max_elements: int, filter_interactive: bool) -> List[Dict]:
        """iOS元素列表实现"""
        try:
            ios_client = self._get_ios_client()
            if not ios_client:
                return [{"error": "❌ iOS客户端未初始化"}]
            
            # 获取iOS页面源码
            elements = []
            
            try:
                # 方法1：使用WDA的source
                source = ios_client.wda.source()
                if source:
                    root = ET.fromstring(source)
                    elements = self._parse_ios_elements(root, max_elements, filter_interactive)
            except:
                pass
            
            # 如果方法1失败，尝试方法2：使用find_elements
            if not elements:
                try:
                    # 获取所有可交互元素
                    interactive_elements = []
                    
                    # 查找按钮
                    buttons = ios_client.wda.find_elements_by_class_name("XCUIElementTypeButton")
                    for btn in buttons:
                        if len(interactive_elements) < max_elements:
                            elements.append(self._convert_ios_element(btn, "Button"))
                    
                    # 查找文本框
                    text_fields = ios_client.wda.find_elements_by_class_name("XCUIElementTypeTextField")
                    for tf in text_fields:
                        if len(elements) < max_elements:
                            elements.append(self._convert_ios_element(tf, "TextField"))
                    
                    # 查找其他可交互元素
                    other_elements = ios_client.wda.find_elements_by_class_name("XCUIElementTypeCell")
                    for elem in other_elements:
                        if len(elements) < max_elements:
                            elements.append(self._convert_ios_element(elem, "Cell"))
                except:
                    pass
            
            return elements[:max_elements]
            
        except Exception as e:
            return [{"error": f"❌ iOS元素解析失败: {e}"}]
    
    def _parse_ios_elements(self, root, max_elements: int, filter_interactive: bool) -> List[Dict]:
        """解析iOS XML元素"""
        elements = []
        
        def parse_ios_node(node, depth=0):
            if depth > 20 or len(elements) >= max_elements:
                return
            
            # 提取iOS元素属性
            elem_type = node.get('type', '')
            name = node.get('name', '')
            label = node.get('label', '')
            value = node.get('value', '')
            visible = node.get('visible', 'false') == 'true'
            enabled = node.get('enabled', 'true') == 'true'
            
            # iOS特有的bounds格式
            bounds_str = node.get('bounds', '')
            x, y, width, height = 0, 0, 0, 0
            if bounds_str:
                match = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds_str)
                if match:
                    x1, y1, x2, y2 = map(int, match.groups())
                    x, y = x1, y1
                    width, height = x2 - x1, y2 - y1
            
            # 判断是否可交互
            interactive_types = [
                'XCUIElementTypeButton', 'XCUIElementTypeTextField', 'XCUIElementTypeSecureTextField',
                'XCUIElementTypeSwitch', 'XCUIElementTypeSlider', 'XCUIElementTypePicker',
                'XCUIElementTypeCell', 'XCUIElementTypeCollectionViewCell'
            ]
            
            is_interactive = elem_type in interactive_types
            
            # 过滤条件
            if filter_interactive and not is_interactive:
                # 递归处理子节点
                for child in node:
                    parse_ios_node(child, depth + 1)
                return
            
            # 构建元素信息
            element = {
                'text': name or label or value or '',
                'type': elem_type,
                'name': name,
                'label': label,
                'value': value,
                'bounds': bounds_str,
                'x': x,
                'y': y,
                'width': width,
                'height': height,
                'clickable': is_interactive,
                'enabled': enabled,
                'visible': visible,
                'depth': depth
            }
            
            elements.append(element)
            
            # 递归处理子节点
            for child in node:
                parse_ios_node(child, depth + 1)
        
        parse_ios_node(root)
        
        # 智能排序
        elements.sort(key=lambda e: (
            not e.get('clickable', False),
            not bool(e.get('text', '')),
            e.get('depth', 0)
        ))
        
        return elements
    
    def _convert_ios_element(self, element, elem_type: str) -> Dict:
        """转换iOS WDA元素为统一格式"""
        try:
            # 获取元素属性
            bounds = element.bounds
            rect = bounds.rect
            
            return {
                'text': element.name or element.label or element.value or '',
                'type': elem_type,
                'name': element.name,
                'label': element.label,
                'value': element.value,
                'bounds': f"[{int(rect.x)},{int(rect.y)}][{int(rect.x + rect.width)},{int(rect.y + rect.height)}]",
                'x': int(rect.x),
                'y': int(rect.y),
                'width': int(rect.width),
                'height': int(rect.height),
                'clickable': True,
                'enabled': element.is_enabled,
                'visible': element.is_displayed,
                'depth': 0
            }
        except Exception as e:
            return {
                'error': f"转换iOS元素失败: {e}",
                'type': elem_type
            }
    
    def find_element_by_text(self, text: str, exact: bool = False) -> Optional[Dict]:
        """根据文本查找元素"""
        elements = self.list_elements(filter_interactive=False)
        
        for elem in elements:
            if 'error' in elem:
                continue
            
            elem_text = elem.get('text', '').lower()
            search_text = text.lower()
            
            if exact:
                if elem_text == search_text:
                    return elem
            else:
                if search_text in elem_text:
                    return elem
        
        return None
    
    def find_element_by_id(self, resource_id: str) -> Optional[Dict]:
        """根据resource-id查找元素"""
        elements = self.list_elements(filter_interactive=False)
        
        for elem in elements:
            if 'error' in elem:
                continue
            
            elem_id = elem.get('resource-id', '')
            if elem_id == resource_id or elem_id.endswith(f":id/{resource_id}"):
                return elem
        
        return None
    
    def get_clickable_elements(self) -> List[Dict]:
        """获取所有可点击元素"""
        elements = self.list_elements(filter_interactive=True)
        return [elem for elem in elements if 'error' not in elem and elem.get('clickable', False)]
    
    def get_elements_by_type(self, elem_type: str) -> List[Dict]:
        """根据类型获取元素"""
        elements = self.list_elements(filter_interactive=False)
        
        return [elem for elem in elements 
                if 'error' not in elem and 
                (elem.get('type', '') == elem_type or elem.get('class', '') == elem_type)]
