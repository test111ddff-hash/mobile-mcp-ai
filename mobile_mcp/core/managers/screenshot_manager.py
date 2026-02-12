#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一截图管理器 - 合并iOS和Android的截图功能

功能：
1. 统一截图接口
2. 自动平台检测
3. 支持压缩、网格、SoM等所有截图模式
"""

import time
import re
from pathlib import Path
from typing import Dict, Optional
from PIL import Image, ImageDraw, ImageFont


class ScreenshotManager:
    """统一截图管理器"""
    
    def __init__(self, mobile_client):
        self.client = mobile_client
        
        # 截图目录
        project_root = Path(__file__).parent.parent.parent
        self.screenshot_dir = project_root / "screenshots"
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
    
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
    
    def _take_raw_screenshot(self, filepath: str) -> tuple:
        """获取原始截图（统一接口）"""
        try:
            screen_width, screen_height = 0, 0
            
            if self._is_ios():
                ios_client = self._get_ios_client()
                if ios_client and hasattr(ios_client, 'wda'):
                    ios_client.wda.screenshot(filepath)
                    size = ios_client.wda.window_size()
                    screen_width, screen_height = size[0], size[1]
                else:
                    raise RuntimeError("iOS客户端未初始化")
            else:
                self.client.u2.screenshot(filepath)
                info = self.client.u2.info
                screen_width = info.get('displayWidth', 0)
                screen_height = info.get('displayHeight', 0)
            
            return screen_width, screen_height
        except Exception as e:
            raise RuntimeError(f"截图失败: {e}")
    
    def take_screenshot(self, description: str = "", compress: bool = True, 
                        max_width: int = 720, quality: int = 75,
                        crop_x: int = 0, crop_y: int = 0, crop_size: int = 0) -> Dict:
        """统一截图接口（支持压缩和局部裁剪）"""
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            platform = "ios" if self._is_ios() else "android"
            
            # 第1步：截图保存为临时 PNG
            temp_filename = f"temp_{timestamp}.png"
            temp_path = self.screenshot_dir / temp_filename
            
            # 获取屏幕尺寸并截图
            screen_width, screen_height = self._take_raw_screenshot(str(temp_path))
            original_size = temp_path.stat().st_size
            
            # 第2步：打开图片
            img = Image.open(temp_path)
            
            # 第2.5步：局部裁剪（如果指定了裁剪参数）
            crop_offset_x, crop_offset_y = 0, 0
            is_cropped = False
            
            if crop_x > 0 and crop_y > 0 and crop_size > 0:
                # 计算裁剪区域（以 crop_x, crop_y 为中心）
                half_size = crop_size // 2
                left = max(0, crop_x - half_size)
                top = max(0, crop_y - half_size)
                right = min(img.width, crop_x + half_size)
                bottom = min(img.height, crop_y + half_size)
                
                # 记录偏移量（用于坐标换算）
                crop_offset_x = left
                crop_offset_y = top
                
                # 裁剪
                img = img.crop((left, top, right, bottom))
                is_cropped = True
            
            # ========== 情况1：局部裁剪截图（不压缩，保持清晰度）==========
            if is_cropped:
                # 生成文件名
                if description:
                    safe_desc = re.sub(r'[^\w\s-]', '', description).strip().replace(' ', '_')
                    filename = f"screenshot_{platform}_crop_{safe_desc}_{timestamp}.png"
                else:
                    filename = f"screenshot_{platform}_crop_{timestamp}.png"
                
                final_path = self.screenshot_dir / filename
                
                # 保存为 PNG（保持清晰度）
                img.save(str(final_path), "PNG")
                
                # 删除临时文件
                temp_path.unlink()
                
                return {
                    "success": True,
                    "screenshot_path": str(final_path),
                    "image_width": img.width,
                    "image_height": img.height,
                    "crop_offset_x": crop_offset_x,
                    "crop_offset_y": crop_offset_y
                }
            
            # ========== 情况2：全屏压缩截图 ==========
            elif compress:
                # 🔴 关键：记录原始图片尺寸（用于坐标转换）
                original_img_width = img.width
                original_img_height = img.height
                
                # 第3步：缩小尺寸（保持宽高比）
                image_width, image_height = img.width, img.height
                
                if img.width > max_width:
                    ratio = max_width / img.width
                    new_w = max_width
                    new_h = int(img.height * ratio)
                    # 兼容不同版本的 Pillow
                    try:
                        resample = Image.Resampling.LANCZOS
                    except AttributeError:
                        try:
                            resample = Image.LANCZOS
                        except AttributeError:
                            resample = Image.ANTIALIAS
                    img = img.resize((new_w, new_h), resample)
                    image_width, image_height = new_w, new_h
                
                # 生成文件名（JPEG 格式）
                if description:
                    safe_desc = re.sub(r'[^\w\s-]', '', description).strip().replace(' ', '_')
                    filename = f"screenshot_{platform}_{safe_desc}_{timestamp}.jpg"
                else:
                    filename = f"screenshot_{platform}_{timestamp}.jpg"
                
                final_path = self.screenshot_dir / filename
                
                # 保存为 JPEG（处理透明通道）
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert("RGB")
                
                img.save(str(final_path), "JPEG", quality=quality)
                temp_path.unlink()
                
                compressed_size = final_path.stat().st_size
                saved_percent = (1 - compressed_size / original_size) * 100
                
                # 返回结果
                return {
                    "success": True,
                    "screenshot_path": str(final_path),
                    "image_width": image_width,
                    "image_height": image_height,
                    "original_img_width": original_img_width,
                    "original_img_height": original_img_height
                }
            
            # ========== 情况3：全屏不压缩截图 ==========
            else:
                if description:
                    safe_desc = re.sub(r'[^\w\s-]', '', description).strip().replace(' ', '_')
                    filename = f"screenshot_{platform}_{safe_desc}_{timestamp}.png"
                else:
                    filename = f"screenshot_{platform}_{timestamp}.png"
                
                final_path = self.screenshot_dir / filename
                temp_path.rename(final_path)
                
                # 返回结果（不压缩时尺寸相同）
                return {
                    "success": True,
                    "screenshot_path": str(final_path),
                    "image_width": img.width,
                    "image_height": img.height
                }
                
        except ImportError:
            return {"success": False, "message": "❌ 需要安装 Pillow: pip install Pillow"}
        except Exception as e:
            return {"success": False, "message": f"❌ 截图失败: {e}"}
    
    def take_screenshot_with_grid(self, grid_size: int = 100, show_popup_hints: bool = False) -> Dict:
        """统一网格截图接口"""
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            platform = "ios" if self._is_ios() else "android"
            
            # 第1步：截图
            temp_filename = f"temp_grid_{timestamp}.png"
            temp_path = self.screenshot_dir / temp_filename
            
            screen_width, screen_height = self._take_raw_screenshot(str(temp_path))
            
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
            
            # 第3步：检测弹窗并标注（仅Android）
            popup_info = None
            close_positions = []
            
            if show_popup_hints and not self._is_ios():
                try:
                    import xml.etree.ElementTree as ET
                    xml_string = self.client.u2.dump_hierarchy(compressed=False)
                    root = ET.fromstring(xml_string)
                    
                    # 使用严格的弹窗检测
                    popup_bounds, popup_confidence = self._detect_popup_with_confidence(
                        root, screen_width, screen_height
                    )
                    
                    if popup_bounds and popup_confidence >= 0.6:
                        px1, py1, px2, py2 = popup_bounds
                        popup_width = px2 - px1
                        popup_height = py2 - py1
                        
                        # 绘制弹窗边框（蓝色）
                        draw.rectangle([px1, py1, px2, py2], outline=(0, 100, 255, 200), width=3)
                        draw.text((px1 + 5, py1 + 5), f"弹窗区域", fill=(0, 100, 255), font=font)
                        
                        # 计算可能的 X 按钮位置
                        offset_x = max(25, int(popup_width * 0.05))
                        offset_y = max(25, int(popup_height * 0.04))
                        outer_offset = max(15, int(popup_width * 0.025))
                        
                        close_positions = [
                            {"name": "右上角内", "x": px2 - offset_x, "y": py1 + offset_y, "priority": 1},
                            {"name": "右上角外", "x": px2 + outer_offset, "y": py1 - outer_offset, "priority": 2},
                            {"name": "正上方", "x": (px1 + px2) // 2, "y": py1 - offset_y, "priority": 3},
                            {"name": "底部下方", "x": (px1 + px2) // 2, "y": py2 + offset_y, "priority": 4},
                        ]
                        
                        # 绘制可能的 X 按钮位置
                        for i, pos in enumerate(close_positions):
                            cx, cy = pos["x"], pos["y"]
                            if 0 <= cx <= img_width and 0 <= cy <= img_height:
                                draw.ellipse([cx-15, cy-15, cx+15, cy+15], 
                                           outline=(0, 255, 0, 200), width=2)
                                draw.text((cx-5, cy-8), str(i+1), fill=(0, 255, 0), font=font)
                                draw.text((cx+18, cy-8), f"({cx},{cy})", fill=(0, 255, 0), font=font_small)
                        
                        popup_info = {
                            "bounds": f"[{px1},{py1}][{px2},{py2}]",
                            "width": px2 - px1,
                            "height": py2 - py1,
                            "close_positions": close_positions
                        }
                
                except Exception:
                    pass  # 弹窗检测失败不影响主功能
            
            # 第4步：保存标注后的截图
            filename = f"screenshot_{platform}_grid_{timestamp}.jpg"
            final_path = self.screenshot_dir / filename
            
            # 转换为 RGB 并保存
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert("RGB")
            
            img.save(str(final_path), "JPEG", quality=85)
            temp_path.unlink()
            
            result = {
                "success": True,
                "screenshot_path": str(final_path),
                "image_width": img_width,
                "image_height": img_height,
                "grid_size": grid_size
            }
            
            if popup_info:
                result["popup"] = popup_info["bounds"]
                if close_positions:
                    result["close_hints"] = [(p['x'], p['y']) for p in close_positions[:3]]
            
            return result
            
        except ImportError:
            return {"success": False, "message": "❌ 需要安装 Pillow: pip install Pillow"}
        except Exception as e:
            return {"success": False, "message": f"❌ 网格截图失败: {e}"}
    
    def take_screenshot_with_som(self) -> Dict:
        """统一SoM截图接口"""
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            platform = "ios" if self._is_ios() else "android"
            
            # 第1步：截图
            temp_filename = f"temp_som_{timestamp}.png"
            temp_path = self.screenshot_dir / temp_filename
            
            screen_width, screen_height = self._take_raw_screenshot(str(temp_path))
            
            img = Image.open(temp_path)
            draw = ImageDraw.Draw(img, 'RGBA')
            img_width, img_height = img.size
            
            # 计算坐标缩放比例
            scale_x = img_width / screen_width if screen_width > 0 else 1.0
            scale_y = img_height / screen_height if screen_height > 0 else 1.0
            
            # 尝试加载字体
            if self._is_ios():
                font_size = int(16 * scale_x)
                font_size_small = int(12 * scale_x)
            else:
                font_size = 16
                font_size_small = 12
            
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
                font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size_small)
            except:
                font = ImageFont.load_default()
                font_small = font
            
            # 第2步：获取所有可点击元素
            elements = []
            if self._is_ios():
                # iOS 使用专门的实现
                ios_client = self._get_ios_client()
                if ios_client and hasattr(ios_client, 'list_elements'):
                    ios_elements = ios_client.list_elements()
                    for elem in ios_elements:
                        bounds_str = elem.get('bounds', '')
                        name = elem.get('name', '')
                        label = elem.get('label', '')
                        value = elem.get('value', '')
                        elem_type = elem.get('type', '')
                        
                        if not bounds_str:
                            continue
                        
                        match = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds_str)
                        if not match:
                            continue
                        
                        # 获取逻辑坐标
                        logical_x1, logical_y1, logical_x2, logical_y2 = map(int, match.groups())
                        
                        # iOS需要转换为物理坐标
                        x1 = int(logical_x1 * scale_x)
                        y1 = int(logical_y1 * scale_y)
                        x2 = int(logical_x2 * scale_x)
                        y2 = int(logical_y2 * scale_y)
                        
                        # 判断是否可点击
                        clickable = elem.get('enabled', False) and elem_type not in ['XCUIElementTypeStatusBar', 'XCUIElementTypeNavigationBar']
                        
                        elements.append({
                            'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
                            'text': name or label or value or '',
                            'type': elem_type,
                            'clickable': clickable
                        })
            else:
                # Android 使用 XML 解析
                import xml.etree.ElementTree as ET
                xml_string = self.client.u2.dump_hierarchy(compressed=False)
                root = ET.fromstring(xml_string)
                
                def parse_android_elements(node, depth=0):
                    if depth > 20:  # 限制深度
                        return
                    
                    # 提取属性
                    bounds_str = node.get('bounds', '')
                    text = node.get('text', '')
                    resource_id = node.get('resource-id', '')
                    class_name = node.get('class', '')
                    clickable = node.get('clickable', 'false') == 'true'
                    
                    if bounds_str:
                        match = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds_str)
                        if match:
                            x1, y1, x2, y2 = map(int, match.groups())
                            
                            # 只添加可点击或有意义的元素
                            if clickable or text or resource_id:
                                elements.append({
                                    'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
                                    'text': text,
                                    'resource_id': resource_id,
                                    'type': class_name.split('.')[-1] if class_name else '',
                                    'clickable': clickable
                                })
                    
                    # 递归处理子节点
                    for child in node:
                        parse_android_elements(child, depth + 1)
                
                parse_android_elements(root)
            
            # 第3步：绘制标注
            clickable_elements = [elem for elem in elements if elem.get('clickable', False)]
            
            # 绘制可点击元素
            for i, elem in enumerate(clickable_elements[:50]):  # 限制数量
                x1, y1, x2, y2 = elem['x1'], elem['y1'], elem['x2'], elem['y2']
                
                # 确保坐标在图片范围内
                x1 = max(0, min(x1, img_width - 1))
                y1 = max(0, min(y1, img_height - 1))
                x2 = max(x1 + 1, min(x2, img_width))
                y2 = max(y1 + 1, min(y2, img_height))
                
                # 绘制边框
                draw.rectangle([x1, y1, x2, y2], outline=(255, 0, 0, 200), width=2)
                
                # 绘制编号
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2
                
                # 绘制背景圆圈
                circle_size = min(20, (x2 - x1) // 2, (y2 - y1) // 2)
                if circle_size > 5:
                    draw.ellipse([center_x - circle_size, center_y - circle_size, 
                                center_x + circle_size, center_y + circle_size],
                               fill=(255, 0, 0, 180))
                    draw.text((center_x - 5, center_y - 8), str(i + 1), 
                             fill=(255, 255, 255), font=font)
            
            # 第4步：保存图片
            filename = f"screenshot_{platform}_som_{timestamp}.jpg"
            final_path = self.screenshot_dir / filename
            
            # 转换为 RGB 并保存
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert("RGB")
            
            img.save(str(final_path), "JPEG", quality=85)
            temp_path.unlink()
            
            return {
                "success": True,
                "screenshot_path": str(final_path),
                "image_width": img_width,
                "image_height": img_height,
                "elements_count": len(clickable_elements),
                "elements": clickable_elements[:50]  # 返回元素列表供后续使用
            }
            
        except ImportError:
            return {"success": False, "message": "❌ 需要安装 Pillow: pip install Pillow"}
        except Exception as e:
            return {"success": False, "message": f"❌ SoM截图失败: {e}"}
    
    def _detect_popup_with_confidence(self, root, screen_width: int, screen_height: int) -> tuple:
        """检测弹窗（Android专用）"""
        try:
            # 弹窗特征检测
            popup_candidates = []
            
            for node in root.iter():
                class_name = node.get('class', '')
                text = node.get('text', '')
                bounds_str = node.get('bounds', '')
                
                if not bounds_str:
                    continue
                
                match = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds_str)
                if not match:
                    continue
                
                x1, y1, x2, y2 = map(int, match.groups())
                width = x2 - x1
                height = y2 - y1
                
                # 弹窗特征
                confidence = 0.0
                
                # 1. 对话框类
                if 'Dialog' in class_name:
                    confidence += 0.4
                
                # 2. 居中显示
                center_x = screen_width // 2
                center_y = screen_height // 2
                popup_center_x = (x1 + x2) // 2
                popup_center_y = (y1 + y2) // 2
                
                if abs(popup_center_x - center_x) < screen_width * 0.1:
                    confidence += 0.2
                if abs(popup_center_y - center_y) < screen_height * 0.2:
                    confidence += 0.2
                
                # 3. 合理的尺寸（屏幕的30%-80%）
                screen_area = screen_width * screen_height
                popup_area = width * height
                area_ratio = popup_area / screen_area
                
                if 0.1 <= area_ratio <= 0.6:
                    confidence += 0.2
                
                if confidence >= 0.6:
                    popup_candidates.append((confidence, (x1, y1, x2, y2)))
            
            if popup_candidates:
                # 返回置信度最高的弹窗
                popup_candidates.sort(key=lambda x: x[0], reverse=True)
                return popup_candidates[0][1], popup_candidates[0][0]
            
            return None, 0.0
        except Exception:
            return None, 0.0
