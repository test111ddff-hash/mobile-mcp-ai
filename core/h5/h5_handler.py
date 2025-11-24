#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
H5处理器 - 智能处理H5/WebView内容

策略：
1. 自动检测页面是否包含WebView
2. 优先使用UIAutomator2的text定位（适用80%场景）
3. 失败时自动切换到Appium context（需要安装Appium）

用法：
    handler = H5Handler(mobile_client)
    result = await handler.smart_click("提交按钮")
"""
import asyncio
from typing import Dict, Optional


class H5Handler:
    """
    H5智能处理器
    
    自动检测并处理H5/WebView内容
    """
    
    def __init__(self, mobile_client):
        """
        初始化H5处理器
        
        Args:
            mobile_client: MobileClient实例
        """
        self.mobile_client = mobile_client
        self.u2 = mobile_client.u2
        
        # 缓存
        self._last_check_time = 0
        self._has_webview_cache = None
        self._cache_ttl = 2  # 缓存2秒
        
        # Appium支持（延迟加载）
        self._appium_driver = None
        self._appium_available = None
    
    async def is_h5_page(self, use_cache: bool = True) -> bool:
        """
        检测当前页面是否包含H5/WebView
        
        Args:
            use_cache: 是否使用缓存
            
        Returns:
            True表示有H5内容
        """
        import time
        
        # 检查缓存
        if use_cache and self._has_webview_cache is not None:
            current_time = time.time()
            if current_time - self._last_check_time < self._cache_ttl:
                return self._has_webview_cache
        
        # 获取页面XML
        xml = self.u2.dump_hierarchy()
        
        # 检测WebView
        has_webview = any([
            'android.webkit.WebView' in xml,
            'com.tencent.smtt.webkit.WebView' in xml,  # X5内核
            'com.uc.webview' in xml,  # UC浏览器内核
            'org.xwalk.core.XWalkView' in xml,  # CrossWalk
        ])
        
        # 更新缓存
        self._has_webview_cache = has_webview
        self._last_check_time = time.time()
        
        return has_webview
    
    async def get_webview_info(self) -> Optional[Dict]:
        """
        获取WebView详细信息
        
        Returns:
            WebView信息字典，无WebView则返回None
        """
        xml = self.u2.dump_hierarchy()
        
        if 'android.webkit.WebView' not in xml:
            return None
        
        # 解析WebView信息
        from xml.etree import ElementTree as ET
        root = ET.fromstring(xml)
        
        webviews = root.findall(".//node[@class='android.webkit.WebView']")
        if not webviews:
            return None
        
        # 返回第一个WebView的信息
        wv = webviews[0]
        
        info = {
            'count': len(webviews),
            'resource_id': wv.get('resource-id', ''),
            'bounds': wv.get('bounds', ''),
            'text': wv.get('text', ''),
            'content_desc': wv.get('content-desc', ''),
            'has_children': len(list(wv)) > 0,
        }
        
        return info
    
    async def smart_click(self, element_desc: str, locator=None) -> Dict:
        """
        智能点击（自动处理H5和原生）
        
        策略：
        1. 先检测是否在WebView中
        2. 优先使用UIAutomator2的text定位（简单快速）
        3. 失败时尝试Appium context切换（复杂H5）
        
        Args:
            element_desc: 元素描述
            locator: SmartLocator实例（可选）
            
        Returns:
            操作结果
        """
        print(f"🎯 H5智能点击: {element_desc}")
        
        # 检测是否在H5页面
        is_h5 = await self.is_h5_page()
        
        if is_h5:
            print(f"   ✅ 检测到H5内容")
            
            # 方案1: UIAutomator2 text定位（适用80%场景）
            print(f"   📱 尝试UIAutomator2定位...")
            
            # 如果提供了locator，使用智能定位
            if locator:
                result = await locator.locate(element_desc)
                if result:
                    click_result = await self.mobile_client.click(
                        element_desc, 
                        ref=result['ref'], 
                        verify=False
                    )
                    if click_result.get('success'):
                        print(f"   ✅ UIAutomator2定位成功")
                        return click_result
            
            # 直接text定位
            try:
                if self.u2(text=element_desc).exists(timeout=1):
                    self.u2(text=element_desc).click()
                    print(f"   ✅ UIAutomator2 text定位成功")
                    return {"success": True, "method": "uiautomator2_text"}
                
                # 尝试description定位
                if self.u2(description=element_desc).exists(timeout=1):
                    self.u2(description=element_desc).click()
                    print(f"   ✅ UIAutomator2 description定位成功")
                    return {"success": True, "method": "uiautomator2_desc"}
                
                # 尝试包含匹配
                if self.u2(textContains=element_desc).exists(timeout=1):
                    self.u2(textContains=element_desc).click()
                    print(f"   ✅ UIAutomator2 textContains定位成功")
                    return {"success": True, "method": "uiautomator2_contains"}
                
            except Exception as e:
                print(f"   ⚠️  UIAutomator2定位失败: {e}")
            
            # 方案2: Appium context切换（复杂H5）
            print(f"   🔄 尝试Appium context切换...")
            appium_result = await self._try_appium_click(element_desc)
            if appium_result.get('success'):
                return appium_result
            
            # 方案3: 坐标点击（最后手段）
            print(f"   📍 尝试坐标点击...")
            return await self._try_coordinate_click(element_desc)
        
        else:
            # 原生页面，直接使用普通定位
            print(f"   📱 原生页面，使用普通定位")
            if locator:
                result = await locator.locate(element_desc)
                if result:
                    return await self.mobile_client.click(
                        element_desc, 
                        ref=result['ref'], 
                        verify=False
                    )
            
            return {"success": False, "reason": "需要提供locator"}
    
    async def smart_input(self, element_desc: str, text: str, locator=None) -> Dict:
        """
        智能输入（自动处理H5和原生）
        
        Args:
            element_desc: 元素描述
            text: 要输入的文本
            locator: SmartLocator实例（可选）
            
        Returns:
            操作结果
        """
        print(f"⌨️  H5智能输入: {element_desc} = {text}")
        
        # 检测是否在H5页面
        is_h5 = await self.is_h5_page()
        
        if is_h5:
            print(f"   ✅ 检测到H5内容")
            
            # 方案1: UIAutomator2定位
            print(f"   📱 尝试UIAutomator2定位...")
            
            if locator:
                result = await locator.locate(element_desc)
                if result:
                    # 🔥 不使用client.type_text，直接操作EditText以支持clear_text
                    ref = result['ref']
                    try:
                        if ref.startswith('com.') or ':' in ref:
                            # resource-id定位
                            edittext = self.u2(resourceId=ref)
                        elif ref.startswith('[') and '][' in ref:
                            # bounds定位 - 不需要处理，直接查找EditText
                            edittext = self.u2(className='android.widget.EditText')
                        else:
                            # text定位 - 🔥 关键：不要用text定位，直接查找EditText
                            # 因为ref可能是TextView的text，而不是EditText的text
                            edittext = self.u2(className='android.widget.EditText')
                        
                        if edittext.exists(timeout=1):
                            edittext.click()
                            await asyncio.sleep(0.5)
                            edittext.clear_text()  # 🔥 关键：先清空
                            await asyncio.sleep(0.3)
                            edittext.set_text(text)
                            await asyncio.sleep(0.5)
                            self.u2.press("back")  # 关闭键盘
                            await asyncio.sleep(0.5)
                            
                            print(f"   ✅ UIAutomator2定位成功")
                            return {"success": True, "method": "uiautomator2_locator"}
                    except Exception as e:
                        print(f"   ⚠️  UIAutomator2定位输入失败: {e}")
            
            # 直接定位EditText
            try:
                # 查找所有EditText
                edittexts = self.u2(className='android.widget.EditText')
                if edittexts.exists(timeout=1):
                    # 找到第一个EditText并输入
                    edittext = self.u2(className='android.widget.EditText')
                    
                    # 🎯 关键：先点击聚焦，清空，再输入
                    edittext.click()
                    await asyncio.sleep(0.5)
                    
                    # 🔥 关键：先清空现有内容
                    edittext.clear_text()
                    await asyncio.sleep(0.3)
                    
                    # 使用set_text输入（支持中文）
                    edittext.set_text(text)
                    await asyncio.sleep(0.5)
                    
                    # 🔥 关键：输入后按back键关闭键盘（不是enter）
                    try:
                        self.u2.press("back")  # 按返回键关闭键盘
                        await asyncio.sleep(0.5)
                    except:
                        pass
                    
                    print(f"   ✅ UIAutomator2输入成功")
                    return {"success": True, "method": "uiautomator2_edittext"}
            except Exception as e:
                print(f"   ⚠️  UIAutomator2输入失败: {e}")
            
            # 方案2: Appium context切换
            print(f"   🔄 尝试Appium context切换...")
            appium_result = await self._try_appium_input(element_desc, text)
            if appium_result.get('success'):
                return appium_result
            
            return {"success": False, "reason": "所有H5输入方法都失败"}
        
        else:
            # 原生页面
            print(f"   📱 原生页面，使用普通输入")
            if locator:
                result = await locator.locate(element_desc)
                if result:
                    return await self.mobile_client.type_text(
                        element_desc, 
                        text, 
                        ref=result['ref']
                    )
            
            return {"success": False, "reason": "需要提供locator"}
    
    async def _try_appium_click(self, element_desc: str) -> Dict:
        """
        尝试使用Appium context切换点击H5元素
        
        Args:
            element_desc: 元素描述
            
        Returns:
            操作结果
        """
        # 检查Appium是否可用
        if not await self._check_appium():
            return {
                "success": False, 
                "reason": "Appium未安装或未启动",
                "suggestion": "pip install Appium-Python-Client"
            }
        
        try:
            # 切换到WebView context
            contexts = self._appium_driver.contexts
            print(f"   📋 可用contexts: {contexts}")
            
            webview_context = None
            for ctx in contexts:
                if 'WEBVIEW' in ctx:
                    webview_context = ctx
                    break
            
            if not webview_context:
                return {"success": False, "reason": "未找到WEBVIEW context"}
            
            # 切换context
            self._appium_driver.switch_to.context(webview_context)
            print(f"   ✅ 已切换到: {webview_context}")
            
            # 使用Selenium定位（H5元素）
            from selenium.webdriver.common.by import By
            
            # 尝试多种定位方式
            selectors = [
                (By.XPATH, f"//*[text()='{element_desc}']"),
                (By.XPATH, f"//button[contains(text(), '{element_desc}')]"),
                (By.XPATH, f"//a[contains(text(), '{element_desc}')]"),
                (By.CSS_SELECTOR, f"button:contains('{element_desc}')"),
            ]
            
            for by, selector in selectors:
                try:
                    element = self._appium_driver.find_element(by, selector)
                    element.click()
                    print(f"   ✅ Appium点击成功: {selector}")
                    
                    # 切回原生context
                    self._appium_driver.switch_to.context('NATIVE_APP')
                    
                    return {"success": True, "method": "appium_webview"}
                except:
                    continue
            
            # 切回原生context
            self._appium_driver.switch_to.context('NATIVE_APP')
            
            return {"success": False, "reason": "Appium未找到元素"}
            
        except Exception as e:
            print(f"   ⚠️  Appium操作失败: {e}")
            return {"success": False, "reason": str(e)}
    
    async def _try_appium_input(self, element_desc: str, text: str) -> Dict:
        """
        尝试使用Appium context切换输入H5元素
        
        Args:
            element_desc: 元素描述
            text: 要输入的文本
            
        Returns:
            操作结果
        """
        if not await self._check_appium():
            return {"success": False, "reason": "Appium未安装"}
        
        try:
            # 切换到WebView context
            contexts = self._appium_driver.contexts
            webview_context = next((c for c in contexts if 'WEBVIEW' in c), None)
            
            if not webview_context:
                return {"success": False, "reason": "未找到WEBVIEW context"}
            
            self._appium_driver.switch_to.context(webview_context)
            
            # 使用Selenium定位输入框
            from selenium.webdriver.common.by import By
            
            selectors = [
                (By.NAME, element_desc),
                (By.ID, element_desc),
                (By.CSS_SELECTOR, f"input[placeholder*='{element_desc}']"),
                (By.XPATH, f"//input[contains(@placeholder, '{element_desc}')]"),
            ]
            
            for by, selector in selectors:
                try:
                    element = self._appium_driver.find_element(by, selector)
                    element.clear()
                    element.send_keys(text)
                    print(f"   ✅ Appium输入成功")
                    
                    # 切回原生context
                    self._appium_driver.switch_to.context('NATIVE_APP')
                    
                    return {"success": True, "method": "appium_webview"}
                except:
                    continue
            
            # 切回原生context
            self._appium_driver.switch_to.context('NATIVE_APP')
            
            return {"success": False, "reason": "Appium未找到输入框"}
            
        except Exception as e:
            return {"success": False, "reason": str(e)}
    
    async def _try_coordinate_click(self, element_desc: str) -> Dict:
        """
        尝试坐标点击（最后手段）
        
        Args:
            element_desc: 元素描述
            
        Returns:
            操作结果
        """
        # 获取WebView信息
        webview_info = await self.get_webview_info()
        
        if not webview_info or not webview_info.get('bounds'):
            return {"success": False, "reason": "无法获取WebView坐标"}
        
        # 解析bounds
        import re
        bounds = webview_info['bounds']
        match = re.search(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds)
        
        if not match:
            return {"success": False, "reason": "无法解析bounds"}
        
        x1, y1, x2, y2 = map(int, match.groups())
        
        # 如果元素描述包含"提交"、"确认"等，点击底部中心
        bottom_keywords = ['提交', '确认', '确定', '保存', '发送', '登录', '注册']
        if any(kw in element_desc for kw in bottom_keywords):
            # 点击WebView底部中心（95%位置）
            center_x = (x1 + x2) // 2
            bottom_y = int(y1 + (y2 - y1) * 0.95)
            
            self.u2.click(center_x, bottom_y)
            print(f"   ✅ 坐标点击成功: ({center_x}, {bottom_y})")
            
            return {"success": True, "method": "coordinate_bottom"}
        
        # 默认点击中心
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2
        
        self.u2.click(center_x, center_y)
        print(f"   ✅ 坐标点击成功: ({center_x}, {center_y})")
        
        return {"success": True, "method": "coordinate_center"}
    
    async def _check_appium(self) -> bool:
        """
        检查Appium是否可用
        
        Returns:
            True表示可用
        """
        # 使用缓存
        if self._appium_available is not None:
            return self._appium_available
        
        try:
            from appium import webdriver
            from appium.options.android import UiAutomator2Options
            
            # 如果还没有driver，尝试创建
            if not self._appium_driver:
                # 获取当前设备信息
                device_info = self.mobile_client.device_manager.check_device_status()
                
                if not device_info.get('connected'):
                    self._appium_available = False
                    return False
                
                # 配置Appium
                options = UiAutomator2Options()
                options.platform_name = 'Android'
                options.device_name = device_info.get('device_id', 'Android')
                options.automation_name = 'UiAutomator2'
                
                # 获取当前App包名
                current_package = await self.mobile_client.get_current_package()
                if current_package:
                    options.app_package = current_package
                    options.app_activity = '.'  # 使用当前Activity
                
                # 连接Appium Server
                self._appium_driver = webdriver.Remote(
                    'http://localhost:4723',
                    options=options
                )
                
                print(f"   ✅ Appium连接成功")
            
            self._appium_available = True
            return True
            
        except ImportError:
            print(f"   ⚠️  Appium未安装: pip install Appium-Python-Client")
            self._appium_available = False
            return False
        except Exception as e:
            print(f"   ⚠️  Appium连接失败: {e}")
            print(f"   💡 提示: 请确保Appium Server已启动（appium）")
            self._appium_available = False
            return False
    
    def close_appium(self):
        """关闭Appium连接"""
        if self._appium_driver:
            try:
                self._appium_driver.quit()
                print(f"✅ Appium连接已关闭")
            except:
                pass
            self._appium_driver = None
            self._appium_available = None

