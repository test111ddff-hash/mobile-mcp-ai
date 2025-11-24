#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
脚本更新工具 - 将坐标保存到测试脚本中

功能：
1. 解析测试脚本
2. 找到对应的步骤
3. 更新坐标（添加注释或替换为坐标格式）
4. 保存文件
"""
import re
import ast
from pathlib import Path
from typing import Dict, Optional, List, Tuple


class ScriptUpdater:
    """脚本更新工具"""
    
    def __init__(self, script_path: str):
        """
        初始化脚本更新工具
        
        Args:
            script_path: 测试脚本路径
        """
        self.script_path = Path(script_path)
        self.script_content = None
        self.script_lines = []
    
    def load_script(self) -> bool:
        """加载脚本文件"""
        try:
            with open(self.script_path, 'r', encoding='utf-8') as f:
                self.script_content = f.read()
                self.script_lines = self.script_content.split('\n')
            return True
        except Exception as e:
            print(f"  ❌ 加载脚本失败: {e}")
            return False
    
    def find_step(self, element_desc: str) -> Optional[Tuple[int, Dict]]:
        """
        查找包含指定元素描述的步骤
        
        Args:
            element_desc: 元素描述
            
        Returns:
            (行号, 步骤信息) 或 None
        """
        for i, line in enumerate(self.script_lines):
            # 查找STEPS列表中的步骤
            if '("点击"' in line or '("输入"' in line:
                # 提取步骤内容
                step_match = re.search(r'\(["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']', line)
                if step_match:
                    action = step_match.group(1)
                    desc = step_match.group(2)
                    
                    if desc == element_desc or element_desc in desc:
                        return (i, {
                            'action': action,
                            'element_desc': desc,
                            'line': line,
                            'line_number': i + 1
                        })
        return None
    
    def update_step_with_coordinate(self, element_desc: str, coordinate: Dict, method: str = 'comment') -> bool:
        """
        更新步骤，添加坐标信息
        
        Args:
            element_desc: 元素描述
            coordinate: 坐标信息 {"x": int, "y": int, "confidence": int}
            method: 更新方式
                - 'comment': 添加注释（推荐，不破坏原有逻辑）
                - 'replace': 替换为坐标格式
        
        Returns:
            是否成功
        """
        if not self.load_script():
            return False
        
        step_info = self.find_step(element_desc)
        if not step_info:
            print(f"  ⚠️  未找到步骤: {element_desc}")
            return False
        
        line_num, step = step_info
        x = coordinate.get('x')
        y = coordinate.get('y')
        confidence = coordinate.get('confidence', 80)
        
        if method == 'comment':
            # 方法1：添加注释（推荐）
            # 格式：("点击", "设置"),  # Cursor AI坐标: [976,159] (置信度:95%)
            comment = f"  # Cursor AI坐标: [{x},{y}] (置信度:{confidence}%)"
            
            # 检查是否已有注释
            if '#' in self.script_lines[line_num]:
                # 已有注释，更新注释
                line = self.script_lines[line_num]
                if 'Cursor AI坐标' in line:
                    # 替换现有坐标注释
                    self.script_lines[line_num] = re.sub(
                        r'# Cursor AI坐标:.*',
                        comment.strip(),
                        line
                    )
                else:
                    # 追加坐标注释
                    self.script_lines[line_num] = line.rstrip() + comment
            else:
                # 没有注释，添加注释
                self.script_lines[line_num] = self.script_lines[line_num].rstrip() + comment
        
        elif method == 'replace':
            # 方法2：替换为坐标格式
            # 格式：("点击", "[976,159][976,159]"),  # 设置 (Cursor AI坐标)
            coord_format = f'"[{x},{y}][{x},{y}]"'
            new_line = f'    ("点击", {coord_format}),  # {element_desc} (Cursor AI坐标, 置信度:{confidence}%)'
            self.script_lines[line_num] = new_line
        
        return True
    
    def save_script(self) -> bool:
        """保存脚本文件"""
        try:
            new_content = '\n'.join(self.script_lines)
            with open(self.script_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"  ✅ 脚本已更新: {self.script_path}")
            return True
        except Exception as e:
            print(f"  ❌ 保存脚本失败: {e}")
            return False
    
    def update_with_coordinate(self, element_desc: str, coordinate: Dict, method: str = 'comment') -> bool:
        """
        更新脚本（完整流程）
        
        Args:
            element_desc: 元素描述
            coordinate: 坐标信息
            method: 更新方式
        
        Returns:
            是否成功
        """
        if self.update_step_with_coordinate(element_desc, coordinate, method):
            return self.save_script()
        return False

