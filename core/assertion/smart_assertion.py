#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能断言系统 - XML分析 + AI视觉识别

策略：
1. 优先XML分析（快速+免费）
2. 失败时降级到AI视觉识别（智能+付费）
3. 支持多种断言类型
"""
from typing import Optional, Dict, Any
import time


class SmartAssertion:
    """智能断言系统"""
    
    def __init__(self, mobile_client):
        """
        初始化智能断言系统
        
        Args:
            mobile_client: MobileClient实例
        """
        self.mobile_client = mobile_client
        
        # 统计
        self.stats = {
            'total': 0,
            'xml_success': 0,
            'ai_success': 0,
            'failed': 0,
            'total_time': 0.0,
        }
    
    async def assert_text_exists(self, text: str, timeout: float = 5.0) -> bool:
        """
        断言：文本存在
        
        Args:
            text: 要查找的文本
            timeout: 超时时间（秒）
        
        Returns:
            True: 找到文本
            False: 未找到文本
        """
        start_time = time.time()
        self.stats['total'] += 1
        
        print(f"\n🔍 断言：文本存在 - '{text}'")
        
        # Level 1: XML文本查找（快速+免费）
        print(f"  📋 Level 1: XML文本查找...")
        xml_result = await self._xml_text_search(text, timeout)
        
        if xml_result:
            self.stats['xml_success'] += 1
            elapsed = (time.time() - start_time) * 1000
            self.stats['total_time'] += elapsed
            print(f"  ✅ XML查找成功！耗时: {elapsed:.2f}ms")
            return True
        
        # Level 2: AI视觉识别（智能+付费）
        print(f"  🤖 Level 2: AI视觉识别...")
        ai_result = await self._ai_visual_search(text)
        
        if ai_result:
            self.stats['ai_success'] += 1
            elapsed = (time.time() - start_time) * 1000
            self.stats['total_time'] += elapsed
            print(f"  ✅ AI识别成功！耗时: {elapsed:.2f}ms")
            return True
        
        # 断言失败
        self.stats['failed'] += 1
        elapsed = (time.time() - start_time) * 1000
        self.stats['total_time'] += elapsed
        print(f"  ❌ 断言失败：未找到文本 '{text}'，耗时: {elapsed:.2f}ms")
        return False
    
    async def assert_element_exists(self, query: str, timeout: float = 5.0) -> bool:
        """
        断言：元素存在
        
        Args:
            query: 元素查询（自然语言）
            timeout: 超时时间（秒）
        
        Returns:
            True: 找到元素
            False: 未找到元素
        """
        start_time = time.time()
        self.stats['total'] += 1
        
        print(f"\n🔍 断言：元素存在 - '{query}'")
        
        # 使用SmartLocator定位元素
        try:
            from ..locator.mobile_smart_locator import MobileSmartLocator
            
            locator = MobileSmartLocator(self.mobile_client)
            result = await locator.locate(query)
            
            if result:
                self.stats['xml_success'] += 1  # 简化统计，实际可能是AI
                elapsed = (time.time() - start_time) * 1000
                self.stats['total_time'] += elapsed
                print(f"  ✅ 元素存在！耗时: {elapsed:.2f}ms")
                return True
            else:
                self.stats['failed'] += 1
                elapsed = (time.time() - start_time) * 1000
                self.stats['total_time'] += elapsed
                print(f"  ❌ 断言失败：未找到元素 '{query}'，耗时: {elapsed:.2f}ms")
                return False
                
        except Exception as e:
            self.stats['failed'] += 1
            elapsed = (time.time() - start_time) * 1000
            self.stats['total_time'] += elapsed
            print(f"  ❌ 断言异常: {e}，耗时: {elapsed:.2f}ms")
            return False
    
    async def assert_visual_exists(self, description: str) -> bool:
        """
        断言：视觉元素存在（纯AI识别）
        
        适用场景：
        - 图标、图片
        - 视觉状态（如"选中"、"高亮"）
        - 布局检查（如"底部有4个图标"）
        
        Args:
            description: 视觉描述
        
        Returns:
            True: 找到元素
            False: 未找到元素
        """
        start_time = time.time()
        self.stats['total'] += 1
        
        print(f"\n🔍 断言：视觉元素存在 - '{description}'")
        
        # 直接使用AI视觉识别
        ai_result = await self._ai_visual_search(description)
        
        if ai_result:
            self.stats['ai_success'] += 1
            elapsed = (time.time() - start_time) * 1000
            self.stats['total_time'] += elapsed
            print(f"  ✅ AI识别成功！耗时: {elapsed:.2f}ms")
            return True
        else:
            self.stats['failed'] += 1
            elapsed = (time.time() - start_time) * 1000
            self.stats['total_time'] += elapsed
            print(f"  ❌ 断言失败：未找到视觉元素 '{description}'，耗时: {elapsed:.2f}ms")
            return False
    
    async def assert_element_enabled(self, query: str) -> bool:
        """
        断言：元素可用（enabled=true）
        
        Args:
            query: 元素查询
        
        Returns:
            True: 元素可用
            False: 元素不可用或不存在
        """
        start_time = time.time()
        self.stats['total'] += 1
        
        print(f"\n🔍 断言：元素可用 - '{query}'")
        
        # 读取XML
        xml_string = self.mobile_client.u2.dump_hierarchy()
        elements = self.mobile_client.xml_parser.parse(xml_string)
        
        # 查找元素
        query_lower = query.lower()
        for elem in elements:
            text = elem.get('text', '').lower()
            desc = elem.get('content_desc', '').lower()
            
            if query_lower in text or query_lower in desc:
                enabled = elem.get('enabled', False)
                
                if enabled:
                    self.stats['xml_success'] += 1
                    elapsed = (time.time() - start_time) * 1000
                    self.stats['total_time'] += elapsed
                    print(f"  ✅ 元素可用！耗时: {elapsed:.2f}ms")
                    return True
                else:
                    self.stats['failed'] += 1
                    elapsed = (time.time() - start_time) * 1000
                    self.stats['total_time'] += elapsed
                    print(f"  ❌ 断言失败：元素不可用，耗时: {elapsed:.2f}ms")
                    return False
        
        # 未找到元素
        self.stats['failed'] += 1
        elapsed = (time.time() - start_time) * 1000
        self.stats['total_time'] += elapsed
        print(f"  ❌ 断言失败：未找到元素 '{query}'，耗时: {elapsed:.2f}ms")
        return False
    
    async def assert_element_count(self, query: str, expected_count: int) -> bool:
        """
        断言：元素数量
        
        Args:
            query: 元素查询
            expected_count: 期望数量
        
        Returns:
            True: 数量匹配
            False: 数量不匹配
        """
        start_time = time.time()
        self.stats['total'] += 1
        
        print(f"\n🔍 断言：元素数量 - '{query}' (期望: {expected_count})")
        
        # 读取XML
        xml_string = self.mobile_client.u2.dump_hierarchy()
        elements = self.mobile_client.xml_parser.parse(xml_string)
        
        # 查找所有匹配元素
        query_lower = query.lower()
        matched = []
        
        for elem in elements:
            text = elem.get('text', '').lower()
            desc = elem.get('content_desc', '').lower()
            
            if query_lower in text or query_lower in desc:
                matched.append(elem)
        
        actual_count = len(matched)
        
        if actual_count == expected_count:
            self.stats['xml_success'] += 1
            elapsed = (time.time() - start_time) * 1000
            self.stats['total_time'] += elapsed
            print(f"  ✅ 数量匹配！实际: {actual_count}，耗时: {elapsed:.2f}ms")
            return True
        else:
            self.stats['failed'] += 1
            elapsed = (time.time() - start_time) * 1000
            self.stats['total_time'] += elapsed
            print(f"  ❌ 断言失败：数量不匹配！期望: {expected_count}，实际: {actual_count}，耗时: {elapsed:.2f}ms")
            return False
    
    # ========================================
    # 内部方法
    # ========================================
    
    async def _xml_text_search(self, text: str, timeout: float) -> bool:
        """
        XML文本查找
        
        Args:
            text: 要查找的文本
            timeout: 超时时间（秒）
        
        Returns:
            True: 找到文本
            False: 未找到文本
        """
        start_time = time.time()
        text_lower = text.lower()
        
        while time.time() - start_time < timeout:
            # 读取XML
            xml_string = self.mobile_client.u2.dump_hierarchy()
            elements = self.mobile_client.xml_parser.parse(xml_string)
            
            # 查找文本
            for elem in elements:
                elem_text = elem.get('text', '').lower()
                elem_desc = elem.get('content_desc', '').lower()
                
                if text_lower in elem_text or text_lower in elem_desc:
                    print(f"     ✅ 找到文本: {elem.get('text') or elem.get('content_desc')}")
                    return True
            
            # 未找到，等待100ms后重试
            await self.mobile_client.wait(0.1)
        
        print(f"     ❌ 超时未找到文本")
        return False
    
    async def _ai_visual_search(self, description: str) -> bool:
        """
        AI视觉识别
        
        Args:
            description: 视觉描述
        
        Returns:
            True: 找到元素
            False: 未找到元素
        """
        try:
            from ...vision.vision_locator import MobileVisionLocator
            
            vision_locator = MobileVisionLocator(self.mobile_client)
            result = await vision_locator.locate_element_by_vision(description)
            
            if result and result.get('found'):
                print(f"     ✅ AI识别成功: {description}")
                return True
            else:
                print(f"     ❌ AI未识别到: {description}")
                return False
                
        except ImportError:
            print(f"     ⚠️  视觉识别模块未安装")
            return False
        except Exception as e:
            print(f"     ⚠️  AI识别失败: {e}")
            return False
    
    def print_stats(self):
        """打印统计信息"""
        print("\n" + "=" * 80)
        print("📊 断言统计")
        print("=" * 80)
        print(f"  总断言次数: {self.stats['total']}")
        print(f"  XML成功: {self.stats['xml_success']} ({self.stats['xml_success']/max(1, self.stats['total'])*100:.1f}%)")
        print(f"  AI成功: {self.stats['ai_success']} ({self.stats['ai_success']/max(1, self.stats['total'])*100:.1f}%)")
        print(f"  失败: {self.stats['failed']} ({self.stats['failed']/max(1, self.stats['total'])*100:.1f}%)")
        print(f"  总耗时: {self.stats['total_time']:.2f}ms")
        print(f"  平均耗时: {self.stats['total_time']/max(1, self.stats['total']):.2f}ms")
        print("=" * 80)

