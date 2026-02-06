#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
iOS客户端 - 使用 facebook-wda（API风格和 uiautomator2 一样）

优势：
1. API和Android端(uiautomator2)几乎完全一致
2. 不需要Appium Server
3. 代码可以跨平台复用

用法:
    client = IOSClientWDA(device_id=None)
    await client.launch_app("com.example.app")
    await client.click("登录")  # 和Android端一样的调用方式！
"""
import asyncio
import sys
import time
from typing import Dict, Optional, List

from core.ios_device_manager_wda import IOSDeviceManagerWDA


class IOSClientWDA:
    """
    iOS客户端 - 使用 facebook-wda
    
    API风格和MobileClient(Android)保持一致
    
    用法:
        client = IOSClientWDA(device_id=None)
        await client.launch_app("com.apple.Preferences")
        await client.click("通用")
    """
    
    def __init__(self, device_id: Optional[str] = None, lazy_connect: bool = False):
        """
        初始化iOS客户端
        
        Args:
            device_id: 设备UDID，None则自动选择第一个设备
            lazy_connect: 是否延迟连接（默认False）
        """
        self.device_manager = IOSDeviceManagerWDA()
        self._device_id = device_id
        self._lazy_connect = lazy_connect
        
        if not lazy_connect:
            self.wda = self.device_manager.connect(device_id)
        else:
            self.wda = None
        
        # 操作历史（用于录制）
        self.operation_history: List[Dict] = []
        
        # 缓存
        self._snapshot_cache = None
        self._cache_timestamp = 0
        self._cache_ttl = 1  # 缓存1秒
    
    def _ensure_connected(self):
        """确保设备已连接"""
        if self.wda is None:
            self.wda = self.device_manager.connect(self._device_id)
    
    async def snapshot(self, use_cache: bool = True) -> str:
        """
        获取页面XML结构
        
        Args:
            use_cache: 是否使用缓存
            
        Returns:
            页面结构字符串
        """
        self._ensure_connected()
        
        # 检查缓存
        if use_cache and self._snapshot_cache:
            current_time = time.time()
            if current_time - self._cache_timestamp < self._cache_ttl:
                return self._snapshot_cache
        
        try:
            # 获取页面源码
            source = self.wda.source()
            
            # 更新缓存
            self._snapshot_cache = source
            self._cache_timestamp = time.time()
            
            return source
        except Exception as e:
            raise RuntimeError(f"获取页面结构失败: {e}")
    
    async def click(self, element: str, ref: Optional[str] = None, verify: bool = True):
        """
        点击元素（API和Android端一致）
        
        Args:
            element: 元素描述（自然语言）
            ref: 元素定位器，支持多种格式：
                - text: 如 "登录"
                - accessibility_id: 如 "login_button"
                - xpath: 如 "//XCUIElementTypeButton[@name='登录']"
                - bounds: 如 "[100,200][300,400]" 或坐标 (x, y)
            verify: 是否验证点击成功
            
        Returns:
            操作结果
        """
        self._ensure_connected()
        
        # 记录操作
        operation_record = {
            'action': 'click',
            'element': element,
            'ref': ref,
            'success': False,
        }
        self.operation_history.append(operation_record)
        
        try:
            if ref:
                # 根据ref类型执行点击
                if ref.startswith('//'):
                    # XPath
                    elem = self.wda(xpath=ref)
                elif ref.startswith('[') and '][' in ref:
                    # bounds坐标 "[x1,y1][x2,y2]"
                    x, y = self._parse_bounds_coords(ref)
                    self.wda.click(x, y)
                    print(f"  ✅ 坐标点击成功: ({x}, {y})", file=sys.stderr)
                    operation_record['success'] = True
                    return {"success": True, "ref": ref}
                elif ',' in ref and ref.replace(',', '').replace(' ', '').isdigit():
                    # 直接坐标 "x,y"
                    parts = ref.split(',')
                    x, y = int(parts[0].strip()), int(parts[1].strip())
                    self.wda.click(x, y)
                    print(f"  ✅ 坐标点击成功: ({x}, {y})", file=sys.stderr)
                    operation_record['success'] = True
                    return {"success": True, "ref": ref}
                else:
                    # 默认尝试多种定位方式
                    elem = self._find_element(ref)
            else:
                # 使用元素描述进行定位
                elem = self._find_element(element)
            
            # 点击元素
            if elem and elem.exists:
                elem.click()
                print(f"  ✅ 点击成功: {ref or element}", file=sys.stderr)
                operation_record['success'] = True
                
                # 等待页面稳定
                await asyncio.sleep(0.3)
                
                return {"success": True, "ref": ref or element}
            else:
                raise ValueError(f"未找到元素: {ref or element}")
            
        except Exception as e:
            operation_record['error'] = str(e)
            print(f"  ❌ 点击失败: {e}", file=sys.stderr)
            return {"success": False, "reason": str(e)}
    
    def _find_element(self, locator: str):
        """
        尝试多种方式定位元素（增强版）
        
        Args:
            locator: 定位器字符串
            
        Returns:
            元素对象或None
        """
        # 尝试顺序：name > label > text > accessibility_id > className > 模糊匹配
        strategies = [
            lambda: self.wda(name=locator),
            lambda: self.wda(label=locator),
            lambda: self.wda(text=locator),
            lambda: self.wda(value=locator),  # 输入框的值
            lambda: self.wda(nameContains=locator),
            lambda: self.wda(labelContains=locator),
            lambda: self.wda(valueContains=locator),
        ]
        
        for strategy in strategies:
            try:
                elem = strategy()
                if elem.exists:
                    return elem
            except:
                continue
        
        # 尝试通过 className 定位（如果locator看起来像类名）
        if 'XCUIElementType' in locator:
            try:
                elem = self.wda(className=locator)
                if elem.exists:
                    return elem
            except:
                pass
        
        return None
    
    async def type_text(self, element: str, text: str, ref: Optional[str] = None, verify: bool = True):
        """
        输入文本（API和Android端一致）
        
        Args:
            element: 元素描述
            text: 要输入的文本
            ref: 元素定位器
            verify: 是否验证输入成功
            
        Returns:
            操作结果
        """
        self._ensure_connected()
        
        # 记录操作
        operation_record = {
            'action': 'type',
            'element': element,
            'text': text,
            'ref': ref,
            'success': False,
        }
        self.operation_history.append(operation_record)
        
        try:
            if ref:
                if ref.startswith('//'):
                    elem = self.wda(xpath=ref)
                else:
                    elem = self._find_element(ref)
            else:
                # 查找第一个输入框
                elem = self.wda(className='XCUIElementTypeTextField')
                if not elem.exists:
                    elem = self.wda(className='XCUIElementTypeSecureTextField')
                if not elem.exists:
                    elem = self._find_element(element)
            
            if elem and elem.exists:
                elem.clear_text()
                elem.set_text(text)
                print(f"  ✅ 输入成功: {text}", file=sys.stderr)
                operation_record['success'] = True
                return {"success": True, "ref": ref or element}
            else:
                raise ValueError(f"未找到输入框: {ref or element}")
            
        except Exception as e:
            operation_record['error'] = str(e)
            print(f"  ❌ 输入失败: {e}", file=sys.stderr)
            return {"success": False, "reason": str(e)}
    
    async def swipe(self, direction: str, distance: int = 500, verify: bool = True):
        """
        滑动操作
        
        Args:
            direction: 滑动方向 ('up', 'down', 'left', 'right')
            distance: 滑动距离（像素）
            verify: 是否验证滑动成功
            
        Returns:
            操作结果
        """
        self._ensure_connected()
        
        try:
            # 获取屏幕尺寸
            window = self.wda.window_size()
            width = window.width
            height = window.height
            
            # 计算滑动坐标
            center_x = width // 2
            center_y = height // 2
            
            direction_map = {
                'up': (center_x, int(height * 0.8), center_x, int(height * 0.2)),
                'down': (center_x, int(height * 0.2), center_x, int(height * 0.8)),
                'left': (int(width * 0.8), center_y, int(width * 0.2), center_y),
                'right': (int(width * 0.2), center_y, int(width * 0.8), center_y),
            }
            
            if direction not in direction_map:
                return {"success": False, "reason": f"不支持的滑动方向: {direction}"}
            
            x1, y1, x2, y2 = direction_map[direction]
            
            print(f"  📍 滑动方向: {direction}, 坐标: ({x1}, {y1}) -> ({x2}, {y2})", file=sys.stderr)
            self.wda.swipe(x1, y1, x2, y2, duration=0.5)
            
            print(f"  ✅ 滑动成功: {direction}", file=sys.stderr)
            return {"success": True, "direction": direction}
            
        except Exception as e:
            print(f"  ❌ 滑动失败: {e}", file=sys.stderr)
            return {"success": False, "reason": str(e)}
    
    async def launch_app(self, bundle_id: str, wait_time: int = 3):
        """
        启动应用
        
        Args:
            bundle_id: 应用Bundle ID，如 'com.apple.Preferences'
            wait_time: 等待时间（秒）
            
        Returns:
            操作结果
        """
        self._ensure_connected()
        
        try:
            print(f"  📱 启动App: {bundle_id}", file=sys.stderr)
            
            # 使用 wda 启动应用
            self.wda.session().app_activate(bundle_id)
            
            # 等待应用启动
            await asyncio.sleep(wait_time)
            
            # 验证是否启动成功
            current = await self.get_current_package()
            if current == bundle_id:
                print(f"  ✅ App启动成功: {bundle_id}", file=sys.stderr)
                return {"success": True, "package": bundle_id}
            else:
                print(f"  ⚠️  App可能未启动成功，当前App: {current}", file=sys.stderr)
                return {"success": True, "package": bundle_id, "warning": f"当前App: {current}"}
            
        except Exception as e:
            print(f"  ❌ App启动失败: {e}", file=sys.stderr)
            return {"success": False, "reason": str(e)}
    
    async def stop_app(self, bundle_id: str):
        """
        停止应用
        
        Args:
            bundle_id: 应用Bundle ID
            
        Returns:
            操作结果
        """
        self._ensure_connected()
        
        try:
            print(f"  📱 停止App: {bundle_id}", file=sys.stderr)
            self.wda.session().app_terminate(bundle_id)
            print(f"  ✅ App已停止: {bundle_id}", file=sys.stderr)
            return {"success": True}
        except Exception as e:
            print(f"  ❌ App停止失败: {e}", file=sys.stderr)
            return {"success": False, "reason": str(e)}
    
    async def get_current_package(self) -> Optional[str]:
        """获取当前前台应用的Bundle ID"""
        self._ensure_connected()
        
        try:
            app_info = self.wda.session().app_current()
            return app_info.get('bundleId')
        except:
            return None
    
    async def press_key(self, key: str, verify: bool = True):
        """
        按键盘按键
        
        Args:
            key: 按键名称，支持：
                - "enter" / "回车" - Enter键
                - "back" / "返回" - 返回（在iOS上是导航返回）
                - "home" - Home键
            verify: 是否验证按键效果
        
        Returns:
            操作结果
        """
        self._ensure_connected()
        
        try:
            key_lower = key.lower()
            
            if key_lower in ['enter', '回车', 'return']:
                # 发送回车键
                self.wda(className='XCUIElementTypeKeyboard').buttons['return'].click()
                print(f"  ✅ 按键成功: Enter", file=sys.stderr)
            elif key_lower in ['back', '返回']:
                # iOS没有真正的返回键，尝试点击导航栏的返回按钮
                back_buttons = [
                    self.wda(name='返回'),
                    self.wda(name='Back'),
                    self.wda(label='返回'),
                    self.wda(label='Back'),
                ]
                clicked = False
                for btn in back_buttons:
                    if btn.exists:
                        btn.click()
                        clicked = True
                        break
                
                if clicked:
                    print(f"  ✅ 返回按钮点击成功", file=sys.stderr)
                else:
                    # 如果没有返回按钮，尝试从左边缘滑动
                    window = self.wda.window_size()
                    self.wda.swipe(0, window.height // 2, window.width // 2, window.height // 2)
                    print(f"  ✅ 边缘滑动返回成功", file=sys.stderr)
            elif key_lower == 'home':
                # 按Home键
                self.wda.home()
                print(f"  ✅ 按键成功: Home", file=sys.stderr)
            else:
                return {"success": False, "reason": f"不支持的按键: {key}"}
            
            return {"success": True, "key": key, "verified": False}
            
        except Exception as e:
            print(f"  ❌ 按键失败: {e}", file=sys.stderr)
            return {"success": False, "reason": str(e)}
    
    async def take_screenshot(self, filename: Optional[str] = None) -> str:
        """
        截图
        
        Args:
            filename: 保存的文件名（可选）
            
        Returns:
            截图文件路径
        """
        self._ensure_connected()
        
        import os
        from datetime import datetime
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ios_screenshot_{timestamp}.png"
        
        # 确保截图目录存在
        screenshots_dir = os.path.join(os.getcwd(), 'screenshots')
        os.makedirs(screenshots_dir, exist_ok=True)
        
        filepath = os.path.join(screenshots_dir, filename)
        
        try:
            # 使用 wda 截图
            self.wda.screenshot(filepath)
            print(f"  📸 截图已保存: {filepath}", file=sys.stderr)
            return filepath
        except Exception as e:
            print(f"  ❌ 截图失败: {e}", file=sys.stderr)
            raise
    
    def _parse_bounds_coords(self, bounds_str: str) -> tuple:
        """
        解析bounds字符串，返回中心点坐标
        
        Args:
            bounds_str: 格式如 "[100,200][300,400]"
            
        Returns:
            (x, y) 中心点坐标
        """
        import re
        match = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds_str)
        if match:
            x1, y1, x2, y2 = map(int, match.groups())
            return ((x1 + x2) // 2, (y1 + y2) // 2)
        return (0, 0)
    
    def get_screen_size(self) -> tuple:
        """获取屏幕尺寸"""
        self._ensure_connected()
        
        window = self.wda.window_size()
        return (window.width, window.height)
    
    def take_screenshot_with_som(self) -> Dict:
        """
        Set-of-Mark 截图：给每个可点击元素标上数字（iOS版本）
        
        在截图上给每个可点击元素画框并标上数字编号。
        AI 看图后直接说"点击 3 号"，然后调用 click_by_som(3) 即可。
        
        Returns:
            包含标注截图和元素列表的字典
        """
        try:
            from PIL import Image, ImageDraw, ImageFont
            import re
            from datetime import datetime
            import os
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 第1步：截图
            temp_filename = f"temp_som_ios_{timestamp}.png"
            screenshots_dir = os.path.join(os.getcwd(), 'screenshots')
            os.makedirs(screenshots_dir, exist_ok=True)
            temp_path = os.path.join(screenshots_dir, temp_filename)
            
            self.wda.screenshot(temp_path)
            
            img = Image.open(temp_path)
            draw = ImageDraw.Draw(img, 'RGBA')
            img_width, img_height = img.size
            
            # 尝试加载字体
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
                font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 12)
            except:
                font = ImageFont.load_default()
                font_small = font
            
            # 第2步：获取所有可点击元素
            elements = []
            
            try:
                source_xml = self.wda.source()
                import xml.etree.ElementTree as ET
                root = ET.fromstring(source_xml)
                
                # 可点击的元素类型
                clickable_types = [
                    'XCUIElementTypeButton',
                    'XCUIElementTypeTextField',
                    'XCUIElementTypeSecureTextField',
                    'XCUIElementTypeCell',
                    'XCUIElementTypeLink',
                    'XCUIElementTypeSwitch',
                    'XCUIElementTypeStaticText',
                ]
                
                for elem in root.iter():
                    elem_type = elem.get('type', '')
                    name = elem.get('name', '')
                    label = elem.get('label', '')
                    value = elem.get('value', '')
                    enabled = elem.get('enabled', 'true').lower() == 'true'
                    visible = elem.get('visible', 'true').lower() == 'true'
                    
                    if not enabled or not visible:
                        continue
                    
                    if elem_type not in clickable_types:
                        continue
                    
                    try:
                        x = int(float(elem.get('x', '0')))
                        y = int(float(elem.get('y', '0')))
                        width = int(float(elem.get('width', '0')))
                        height = int(float(elem.get('height', '0')))
                        
                        # 过滤太小或太大的元素
                        if width < 20 or height < 20:
                            continue
                        if width >= img_width * 0.98 and height >= img_height * 0.5:
                            continue
                        
                        center_x = x + width // 2
                        center_y = y + height // 2
                        
                        # 生成描述
                        desc = name or label or value or elem_type.replace('XCUIElementType', '')
                        if len(desc) > 20:
                            desc = desc[:17] + "..."
                        
                        elements.append({
                            'bounds': (x, y, x + width, y + height),
                            'center': (center_x, center_y),
                            'text': name or label or value,
                            'desc': desc,
                            'type': elem_type,
                        })
                    except (ValueError, TypeError):
                        continue
            
            except Exception as e:
                print(f"  ⚠️  获取元素列表失败: {e}", file=sys.stderr)
            
            # 第3步：在截图上标注
            som_elements = []
            
            for idx, elem in enumerate(elements, start=1):
                x1, y1, x2, y2 = elem['bounds']
                center_x, center_y = elem['center']
                
                # 绘制边框（半透明蓝色）
                draw.rectangle([x1, y1, x2, y2], outline=(0, 120, 255, 200), width=2)
                
                # 绘制编号标签（左上角）
                label_text = str(idx)
                
                # 计算标签背景大小
                try:
                    bbox = draw.textbbox((0, 0), label_text, font=font)
                    label_width = bbox[2] - bbox[0] + 8
                    label_height = bbox[3] - bbox[1] + 4
                except:
                    label_width = 30
                    label_height = 20
                
                # 绘制标签背景（红色）
                draw.rectangle(
                    [x1, y1 - label_height, x1 + label_width, y1],
                    fill=(255, 0, 0, 220)
                )
                
                # 绘制编号文字（白色）
                draw.text((x1 + 4, y1 - label_height + 2), label_text, fill=(255, 255, 255), font=font)
                
                # 记录元素信息
                som_elements.append({
                    'id': idx,
                    'desc': elem['desc'],
                    'type': elem['type'].replace('XCUIElementType', ''),
                    'center': elem['center'],
                    'bounds': f"[{x1},{y1}][{x2},{y2}]"
                })
            
            # 第4步：保存标注后的截图
            filename = f"screenshot_ios_som_{timestamp}.jpg"
            final_path = os.path.join(screenshots_dir, filename)
            
            # 转换为 RGB 并保存
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert("RGB")
            
            img.save(final_path, "JPEG", quality=85)
            
            # 删除临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            print(f"  📸 SOM截图已保存: {final_path}", file=sys.stderr)
            print(f"  🔢 标注了 {len(som_elements)} 个元素", file=sys.stderr)
            
            return {
                "success": True,
                "screenshot_path": final_path,
                "elements": som_elements,
                "count": len(som_elements),
                "image_width": img_width,
                "image_height": img_height
            }
            
        except ImportError:
            return {"success": False, "message": "❌ 需要安装 Pillow: pip install Pillow"}
        except Exception as e:
            return {"success": False, "message": f"❌ SOM截图失败: {e}"}
    
    def take_screenshot_with_grid(self, grid_size: int = 100) -> Dict:
        """
        截图并添加网格坐标标注（iOS版本）
        
        在截图上绘制网格线和坐标刻度，帮助快速定位元素位置。
        
        Args:
            grid_size: 网格间距（像素），默认 100
        
        Returns:
            包含标注截图路径的字典
        """
        try:
            from PIL import Image, ImageDraw, ImageFont
            from datetime import datetime
            import os
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 第1步：截图
            temp_filename = f"temp_grid_ios_{timestamp}.png"
            screenshots_dir = os.path.join(os.getcwd(), 'screenshots')
            os.makedirs(screenshots_dir, exist_ok=True)
            temp_path = os.path.join(screenshots_dir, temp_filename)
            
            self.wda.screenshot(temp_path)
            
            img = Image.open(temp_path)
            draw = ImageDraw.Draw(img, 'RGBA')
            
            # 尝试加载字体
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 14)
                font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 11)
            except:
                font = ImageFont.load_default()
                font_small = font
            
            img_width, img_height = img.size
            
            # 第2步：绘制网格线和坐标
            grid_color = (255, 0, 0, 80)  # 半透明红色
            text_color = (255, 0, 0, 200)  # 红色文字
            
            # 绘制垂直网格线
            for x in range(0, img_width, grid_size):
                draw.line([(x, 0), (x, img_height)], fill=grid_color, width=1)
                # 顶部标注 X 坐标
                draw.text((x + 2, 2), str(x), fill=text_color, font=font_small)
            
            # 绘制水平网格线
            for y in range(0, img_height, grid_size):
                draw.line([(0, y), (img_width, y)], fill=grid_color, width=1)
                # 左侧标注 Y 坐标
                draw.text((2, y + 2), str(y), fill=text_color, font=font_small)
            
            # 第3步：保存标注后的截图
            filename = f"screenshot_ios_grid_{timestamp}.jpg"
            final_path = os.path.join(screenshots_dir, filename)
            
            # 转换为 RGB 并保存
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert("RGB")
            
            img.save(final_path, "JPEG", quality=85)
            
            # 删除临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            print(f"  📸 网格截图已保存: {final_path}", file=sys.stderr)
            
            return {
                "success": True,
                "screenshot_path": final_path,
                "image_width": img_width,
                "image_height": img_height,
                "grid_size": grid_size
            }
            
        except ImportError:
            return {"success": False, "message": "❌ 需要安装 Pillow: pip install Pillow"}
        except Exception as e:
            return {"success": False, "message": f"❌ 网格截图失败: {e}"}
    
    def list_elements(self) -> List[Dict]:
        """
        列出所有可交互元素（类似Android的mobile_list_elements）
        
        Returns:
            元素列表
        """
        self._ensure_connected()
        
        elements = []
        
        try:
            # 获取页面源码（XML格式）
            source_xml = self.wda.source()
            
            # 解析XML
            import xml.etree.ElementTree as ET
            root = ET.fromstring(source_xml)
            
            # 只收集可交互的元素类型
            interactable_types = [
                'XCUIElementTypeButton',
                'XCUIElementTypeTextField',
                'XCUIElementTypeSecureTextField',
                'XCUIElementTypeTextView',
                'XCUIElementTypeSwitch',
                'XCUIElementTypeSlider',
                'XCUIElementTypeLink',
                'XCUIElementTypeCell',
                'XCUIElementTypeStaticText',
                'XCUIElementTypeImage',
                'XCUIElementTypeIcon',
            ]
            
            # 递归遍历所有元素
            for elem in root.iter():
                elem_type = elem.get('type', '')
                name = elem.get('name', '')
                label = elem.get('label', '')
                value = elem.get('value', '')
                enabled = elem.get('enabled', 'true').lower() == 'true'
                visible = elem.get('visible', 'true').lower() == 'true'
                
                # 获取坐标信息
                x = elem.get('x', '0')
                y = elem.get('y', '0')
                width = elem.get('width', '0')
                height = elem.get('height', '0')
                
                # 只收集可交互、可见且有文本的元素
                if elem_type in interactable_types and enabled and visible:
                    try:
                        x_int = int(float(x))
                        y_int = int(float(y))
                        w_int = int(float(width))
                        h_int = int(float(height))
                        
                        # 过滤太小的元素
                        if w_int < 10 or h_int < 10:
                            continue
                        
                        elements.append({
                            'type': elem_type,
                            'name': name,
                            'label': label,
                            'value': value,
                            'bounds': f"[{x_int},{y_int}][{x_int + w_int},{y_int + h_int}]",
                            'enabled': enabled,
                            'visible': visible,
                        })
                    except (ValueError, TypeError):
                        # 坐标解析失败，跳过
                        continue
            
            print(f"  📋 找到 {len(elements)} 个可交互元素", file=sys.stderr)
            
        except Exception as e:
            print(f"  ⚠️  获取元素列表失败: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
        
        return elements
    
    def detect_popup(self) -> Dict:
        """
        检测iOS弹窗（类似Android版本）
        
        Returns:
            {
                'has_popup': bool,
                'popup_type': str,  # 'alert', 'sheet', 'custom'
                'bounds': str,  # 弹窗边界
                'confidence': float  # 置信度
            }
        """
        self._ensure_connected()
        
        try:
            # 获取页面源码
            source_xml = self.wda.source()
            
            import xml.etree.ElementTree as ET
            root = ET.fromstring(source_xml)
            
            # 获取屏幕尺寸
            size = self.wda.window_size()
            screen_width, screen_height = size[0], size[1]
            screen_area = screen_width * screen_height
            
            # iOS弹窗类型
            popup_types = {
                'XCUIElementTypeAlert': 'alert',
                'XCUIElementTypeSheet': 'sheet',
                'XCUIElementTypeDialog': 'dialog',
            }
            
            popup_candidates = []
            
            # 遍历所有元素
            for elem in root.iter():
                elem_type = elem.get('type', '')
                name = elem.get('name', '')
                visible = elem.get('visible', 'true').lower() == 'true'
                
                if not visible:
                    continue
                
                # 检查是否是系统弹窗类型
                if elem_type in popup_types:
                    x = int(float(elem.get('x', '0')))
                    y = int(float(elem.get('y', '0')))
                    width = int(float(elem.get('width', '0')))
                    height = int(float(elem.get('height', '0')))
                    
                    popup_candidates.append({
                        'type': popup_types[elem_type],
                        'bounds': f"[{x},{y}][{x + width},{y + height}]",
                        'confidence': 0.9,  # 系统弹窗置信度高
                        'name': name,
                    })
                    continue
                
                # 检查自定义弹窗（大面积居中容器）
                if elem_type in ['XCUIElementTypeOther', 'XCUIElementTypeWindow']:
                    try:
                        x = int(float(elem.get('x', '0')))
                        y = int(float(elem.get('y', '0')))
                        width = int(float(elem.get('width', '0')))
                        height = int(float(elem.get('height', '0')))
                        
                        area = width * height
                        area_ratio = area / screen_area if screen_area > 0 else 0
                        
                        # 自定义弹窗特征：
                        # 1. 面积占屏幕20%-80%
                        # 2. 不是全屏
                        # 3. 相对居中
                        if 0.2 < area_ratio < 0.8:
                            center_x = x + width / 2
                            center_y = y + height / 2
                            screen_center_x = screen_width / 2
                            screen_center_y = screen_height / 2
                            
                            # 计算偏离中心的距离
                            offset_x = abs(center_x - screen_center_x) / screen_width
                            offset_y = abs(center_y - screen_center_y) / screen_height
                            
                            # 如果相对居中（偏离不超过20%）
                            if offset_x < 0.2 and offset_y < 0.2:
                                confidence = 0.7 - (offset_x + offset_y)  # 越居中置信度越高
                                
                                popup_candidates.append({
                                    'type': 'custom',
                                    'bounds': f"[{x},{y}][{x + width},{y + height}]",
                                    'confidence': confidence,
                                    'name': name,
                                })
                    except (ValueError, TypeError):
                        continue
            
            if not popup_candidates:
                return {
                    'has_popup': False,
                    'popup_type': None,
                    'bounds': None,
                    'confidence': 0.0
                }
            
            # 选择置信度最高的
            best = max(popup_candidates, key=lambda x: x['confidence'])
            
            return {
                'has_popup': True,
                'popup_type': best['type'],
                'bounds': best['bounds'],
                'confidence': best['confidence'],
                'name': best.get('name', '')
            }
            
        except Exception as e:
            print(f"  ⚠️  弹窗检测失败: {e}", file=sys.stderr)
            return {
                'has_popup': False,
                'popup_type': None,
                'bounds': None,
                'confidence': 0.0,
                'error': str(e)
            }
    
    def close_popup(self) -> Dict:
        """
        智能关闭iOS弹窗（类似Android版本）
        
        策略：
        1. 检测系统Alert/Sheet - 查找"取消"、"关闭"等按钮
        2. 检测自定义弹窗 - 查找×、关闭按钮
        3. 在弹窗边界内查找小尺寸可点击元素
        
        Returns:
            操作结果
        """
        self._ensure_connected()
        
        try:
            # 先检测弹窗
            popup_info = self.detect_popup()
            
            if not popup_info['has_popup']:
                return {
                    'success': True,
                    'popup': False,
                    'message': '未检测到弹窗'
                }
            
            print(f"  🔍 检测到弹窗: {popup_info['popup_type']}", file=sys.stderr)
            
            # 获取页面源码
            source_xml = self.wda.source()
            
            import xml.etree.ElementTree as ET
            import re
            root = ET.fromstring(source_xml)
            
            # 获取屏幕尺寸
            size = self.wda.window_size()
            screen_width, screen_height = size[0], size[1]
            
            # 解析弹窗边界
            popup_bounds = None
            if popup_info['bounds']:
                match = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', popup_info['bounds'])
                if match:
                    popup_bounds = tuple(map(int, match.groups()))
            
            # 关闭按钮的文本特征
            close_texts = ['×', 'X', 'x', '关闭', '取消', 'Close', 'Cancel', 'Dismiss', '跳过', '知道了', 'OK', '确定']
            
            close_candidates = []
            
            # 遍历所有元素查找关闭按钮
            for elem in root.iter():
                elem_type = elem.get('type', '')
                name = elem.get('name', '')
                label = elem.get('label', '')
                value = elem.get('value', '')
                enabled = elem.get('enabled', 'true').lower() == 'true'
                visible = elem.get('visible', 'true').lower() == 'true'
                
                if not enabled or not visible:
                    continue
                
                try:
                    x = int(float(elem.get('x', '0')))
                    y = int(float(elem.get('y', '0')))
                    width = int(float(elem.get('width', '0')))
                    height = int(float(elem.get('height', '0')))
                    
                    if width < 10 or height < 10:
                        continue
                    
                    center_x = x + width / 2
                    center_y = y + height / 2
                    
                    # 检查是否在弹窗范围内
                    in_popup = True
                    if popup_bounds:
                        px1, py1, px2, py2 = popup_bounds
                        # 扩大搜索范围（关闭按钮可能在弹窗外侧）
                        margin = 100
                        in_popup = (px1 - margin <= center_x <= px2 + margin and 
                                   py1 - margin <= center_y <= py2 + margin)
                    
                    if not in_popup:
                        continue
                    
                    score = 0
                    match_type = ""
                    
                    # 策略1: 精确匹配关闭文本
                    if name in close_texts or label in close_texts or value in close_texts:
                        score = 15.0
                        match_type = f"text='{name or label or value}'"
                    
                    # 策略2: 包含关闭关键词
                    elif any(kw in (name + label + value).lower() for kw in ['close', 'cancel', 'dismiss', '关闭', '取消']):
                        score = 12.0
                        match_type = "keyword"
                    
                    # 策略3: Button类型的小元素
                    elif elem_type == 'XCUIElementTypeButton':
                        if 20 <= width <= 100 and 20 <= height <= 100:
                            score = 8.0
                            match_type = "small_button"
                            
                            # 位置加分（右上角、左上角）
                            rel_x = center_x / screen_width
                            rel_y = center_y / screen_height
                            
                            if rel_y < 0.3:  # 上半部分
                                if rel_x > 0.7:  # 右上角
                                    score += 3.0
                                elif rel_x < 0.3:  # 左上角
                                    score += 2.0
                    
                    # 策略4: Image/Icon类型的小元素
                    elif elem_type in ['XCUIElementTypeImage', 'XCUIElementTypeIcon']:
                        if 15 <= width <= 80 and 15 <= height <= 80:
                            score = 6.0
                            match_type = "small_image"
                            
                            # 位置加分
                            rel_x = center_x / screen_width
                            rel_y = center_y / screen_height
                            
                            if rel_y < 0.3 and rel_x > 0.7:  # 右上角
                                score += 4.0
                    
                    if score > 0:
                        close_candidates.append({
                            'x': int(center_x),
                            'y': int(center_y),
                            'width': width,
                            'height': height,
                            'score': score,
                            'match_type': match_type,
                            'name': name,
                            'label': label,
                        })
                
                except (ValueError, TypeError):
                    continue
            
            if not close_candidates:
                return {
                    'success': False,
                    'popup': True,
                    'fallback': 'vision',
                    'message': '未找到关闭按钮，建议使用视觉识别'
                }
            
            # 选择得分最高的
            best = max(close_candidates, key=lambda x: x['score'])
            
            print(f"  🎯 找到关闭按钮: {best['match_type']} at ({best['x']}, {best['y']})", file=sys.stderr)
            
            # 点击关闭按钮
            self.wda.click(best['x'], best['y'])
            
            # 等待弹窗关闭（使用time.sleep而不是asyncio.sleep）
            time.sleep(0.5)
            
            # 验证弹窗是否关闭
            popup_info_after = self.detect_popup()
            
            if not popup_info_after['has_popup']:
                print(f"  ✅ 弹窗已关闭", file=sys.stderr)
                return {
                    'success': True,
                    'popup': True,
                    'clicked': True,
                    'method': best['match_type']
                }
            else:
                print(f"  ⚠️  弹窗可能未关闭", file=sys.stderr)
                return {
                    'success': False,
                    'popup': True,
                    'clicked': True,
                    'message': '点击后弹窗仍存在'
                }
            
        except Exception as e:
            print(f"  ❌ 关闭弹窗失败: {e}", file=sys.stderr)
            return {
                'success': False,
                'popup': True,
                'error': str(e)
            }































