#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自然语言驱动的测试执行器

功能：
1. 解析自然语言测试步骤
2. 调用MCP工具执行
3. Cursor AI分析XML定位元素
4. 失败时自动视觉识别
5. 生成Python测试模板
"""
import asyncio
import json
import re
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime


class NLTestRunner:
    """自然语言测试执行器"""
    
    def __init__(self, mcp_tools=None, locator=None, mobile_client=None, script_path=None):
        """
        初始化自然语言测试执行器
        
        Args:
            mcp_tools: MCP工具字典（mobile_click, mobile_input等）
            locator: MobileSmartLocator实例（用于XML分析）
            mobile_client: MobileClient实例（用于视觉识别）
            script_path: 脚本路径（用于更新用例）
        """
        self.mcp_tools = mcp_tools or {}
        self.locator = locator
        self.mobile_client = mobile_client
        self.script_path = script_path
        self.execution_log = []  # 执行日志
        self.steps = []  # 解析后的步骤
        self.current_step_index = 0
    
    def parse_natural_language(self, nl_text: str) -> List[Dict]:
        """
        解析自然语言测试步骤
        
        Args:
            nl_text: 自然语言描述，如：
                "启动应用com.im30.way，点击底部第四个图标，点击设置，点击语言，点击English，点击保存"
        
        Returns:
            步骤列表
        """
        steps = []
        
        # 简单规则匹配（可以后续用Cursor AI增强）
        # 匹配模式：
        # - 启动应用xxx
        # - 点击xxx
        # - 输入xxx为xxx
        # - 滑动xxx
        # - 等待x秒
        # - 断言xxx
        
        # 分割步骤（按逗号、句号、换行）
        parts = re.split(r'[，,。.\n]', nl_text.strip())
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
            
            # 启动应用
            if '启动应用' in part or '启动' in part or '打开应用' in part or '打开' in part:
                package_match = re.search(r'com\.\w+(?:\.\w+)*', part)
                if package_match:
                    steps.append({
                        'action': 'launch_app',
                        'package': package_match.group(),
                        'original_text': part
                    })
                    continue  # 找到后继续下一个
            
            # 点击
            elif '点击' in part:
                # 提取元素描述
                element = part.replace('点击', '').strip()
                steps.append({
                    'action': 'click',
                    'element': element,
                    'original_text': part
                })
            
            # 输入
            elif '输入' in part:
                # 匹配：输入xxx为xxx 或 输入xxx xxx
                input_match = re.search(r'输入(.+?)(?:为|：|:)(.+)', part)
                if input_match:
                    element = input_match.group(1).strip()
                    text = input_match.group(2).strip()
                    steps.append({
                        'action': 'input',
                        'element': element,
                        'text': text,
                        'original_text': part
                    })
                else:
                    # 简单匹配：输入xxx
                    element = part.replace('输入', '').strip()
                    steps.append({
                        'action': 'input',
                        'element': element,
                        'text': '',  # 需要后续补充
                        'original_text': part
                    })
            
            # 滑动
            elif '滑动' in part:
                direction = None
                if '上' in part or 'up' in part.lower():
                    direction = 'up'
                elif '下' in part or 'down' in part.lower():
                    direction = 'down'
                elif '左' in part or 'left' in part.lower():
                    direction = 'left'
                elif '右' in part or 'right' in part.lower():
                    direction = 'right'
                
                if direction:
                    steps.append({
                        'action': 'swipe',
                        'direction': direction,
                        'original_text': part
                    })
            
            # 等待
            elif '等待' in part:
                wait_match = re.search(r'(\d+)', part)
                if wait_match:
                    seconds = int(wait_match.group(1))
                    steps.append({
                        'action': 'wait',
                        'seconds': seconds,
                        'original_text': part
                    })
            
            # 断言
            elif '断言' in part or '验证' in part or '检查' in part:
                text_match = re.search(r'["\'](.+?)["\']', part)
                if text_match:
                    text = text_match.group(1)
                    steps.append({
                        'action': 'assert_text',
                        'text': text,
                        'original_text': part
                    })
        
        self.steps = steps
        return steps
    
    async def execute_step(self, step: Dict, step_index: int) -> Dict:
        """
        执行单个步骤
        
        Args:
            step: 步骤信息
            step_index: 步骤索引
        
        Returns:
            执行结果
        """
        action = step.get('action')
        original_text = step.get('original_text', '')
        
        print(f"\n{'='*60}")
        print(f"📋 步骤 {step_index + 1}: {original_text}")
        print(f"{'='*60}")
        
        result = {
            'step_index': step_index,
            'action': action,
            'original_text': original_text,
            'success': False,
            'method': None,
            'element_ref': None,
            'coordinate': None,
            'error': None,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            if action == 'launch_app':
                package = step.get('package')
                print(f"🚀 启动应用: {package}")
                if 'mobile_launch_app' in self.mcp_tools:
                    await self.mcp_tools['mobile_launch_app'](package_name=package, wait_time=3)
                    result['success'] = True
                    result['method'] = 'mcp_launch_app'
                else:
                    raise ValueError("mobile_launch_app工具不可用")
            
            elif action == 'click':
                element = step.get('element')
                print(f"🖱️  点击: {element}")
                
                # 先获取XML
                print(f"  📋 步骤1: 获取页面XML...")
                xml_result = await self._get_xml_snapshot()
                
                # Cursor AI分析XML（这里需要调用Cursor AI）
                print(f"  🤖 步骤2: Cursor AI分析XML定位元素...")
                locate_result = await self._cursor_ai_analyze_xml(xml_result, element)
                
                if locate_result and locate_result.get('found'):
                    # 找到元素，直接使用定位结果执行点击（避免重复定位）
                    element_ref = locate_result.get('ref')
                    result['element_ref'] = element_ref
                    result['method'] = locate_result.get('method', 'xml_analysis')
                    
                    print(f"  ✅ 定位成功: {element_ref}")
                    print(f"  🖱️  步骤3: 执行点击...")
                    
                    # 直接使用client点击，避免MCP工具重复定位
                    if self.mobile_client:
                        try:
                            click_result = await self.mobile_client.click(element, ref=element_ref, verify=False)
                            if click_result.get('success'):
                                result['success'] = True
                            else:
                                result['error'] = click_result.get('reason', '点击失败')
                        except Exception as e:
                            result['error'] = f"点击异常: {e}"
                    else:
                        # 降级：使用MCP工具
                        if 'mobile_click' in self.mcp_tools:
                            click_result = await self.mcp_tools['mobile_click'](element_desc=element)
                            if click_result and click_result.get('success'):
                                result['success'] = True
                            else:
                                result['error'] = click_result.get('error', '点击失败')
                        else:
                            raise ValueError("mobile_click工具不可用")
                else:
                    # XML分析失败，使用视觉识别
                    print(f"  ⚠️  XML分析失败，使用视觉识别...")
                    vision_result = await self._cursor_ai_vision_recognize(element)
                    
                    if vision_result and vision_result.get('coordinate'):
                        coord = vision_result['coordinate']
                        x, y = coord['x'], coord['y']
                        result['coordinate'] = coord
                        result['method'] = 'vision_recognition'
                        
                        print(f"  ✅ 视觉识别成功: ({x}, {y})")
                        print(f"  🖱️  步骤3: 使用坐标点击...")
                        
                        # 直接使用坐标点击（不通过MCP工具，避免重复定位）
                        if self.mobile_client:
                            try:
                                self.mobile_client.u2.click(x, y)
                                result['success'] = True
                                print(f"  ✅ 坐标点击成功")
                            except Exception as e:
                                result['error'] = f"坐标点击失败: {e}"
                        else:
                            result['error'] = "mobile_client不可用，无法执行坐标点击"
                    else:
                        result['error'] = "无法定位元素（XML分析和视觉识别都失败）"
            
            elif action == 'input':
                element = step.get('element')
                text = step.get('text')
                print(f"⌨️  输入: {element} = {text}")
                
                # 获取XML并分析
                xml_result = await self._get_xml_snapshot()
                locate_result = await self._cursor_ai_analyze_xml(xml_result, element)
                
                if locate_result and locate_result.get('found'):
                    element_ref = locate_result.get('ref')
                    result['element_ref'] = element_ref
                    result['method'] = locate_result.get('method', 'xml_analysis')
                    
                    if 'mobile_input' in self.mcp_tools:
                        await self.mcp_tools['mobile_input'](element_desc=element, text=text)
                        result['success'] = True
                    else:
                        raise ValueError("mobile_input工具不可用")
                else:
                    result['error'] = "无法定位输入框"
            
            elif action == 'swipe':
                direction = step.get('direction')
                print(f"👆 滑动: {direction}")
                
                if 'mobile_swipe' in self.mcp_tools:
                    swipe_result = await self.mcp_tools['mobile_swipe'](direction=direction)
                    if swipe_result and swipe_result.get('success'):
                        result['success'] = True
                    else:
                        result['error'] = swipe_result.get('error', '滑动失败')
                else:
                    raise ValueError("mobile_swipe工具不可用")
            
            elif action == 'wait':
                seconds = step.get('seconds', 1)
                print(f"⏳ 等待: {seconds}秒")
                await asyncio.sleep(seconds)
                result['success'] = True
            
            elif action == 'assert_text':
                text = step.get('text')
                print(f"✅ 断言: 检查文本 '{text}'")
                
                if 'mobile_assert_text' in self.mcp_tools:
                    assert_result = await self.mcp_tools['mobile_assert_text'](text=text)
                    if assert_result and assert_result.get('found'):
                        result['success'] = True
                    else:
                        result['error'] = f"未找到文本: {text}"
                else:
                    raise ValueError("mobile_assert_text工具不可用")
        
        except Exception as e:
            result['error'] = str(e)
            print(f"  ❌ 执行失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 记录执行日志
        self.execution_log.append(result)
        
        if result['success']:
            print(f"  ✅ 步骤执行成功")
        else:
            print(f"  ❌ 步骤执行失败: {result.get('error')}")
        
        return result
    
    async def _get_xml_snapshot(self) -> Dict:
        """获取XML快照"""
        if 'mobile_snapshot' in self.mcp_tools:
            snapshot_result = await self.mcp_tools['mobile_snapshot']()
            if snapshot_result and snapshot_result.get('success'):
                return {
                    'xml': snapshot_result.get('snapshot', ''),
                    'success': True
                }
        return {'success': False, 'xml': ''}
    
    async def _cursor_ai_analyze_xml(self, xml_result: Dict, element_desc: str) -> Optional[Dict]:
        """
        Cursor AI分析XML定位元素
        
        使用现有的MobileSmartLocator进行定位
        """
        if not xml_result.get('success'):
            return None
        
        # 🎯 使用现有的locator进行定位
        # 注意：这里需要传入locator实例
        if hasattr(self, 'locator') and self.locator:
            try:
                result = await self.locator.locate(element_desc)
                if result:
                    return {
                        'found': True,
                        'ref': result.get('ref', ''),
                        'method': result.get('method', 'xml_analysis'),
                        'confidence': result.get('confidence', 80)
                    }
            except Exception as e:
                print(f"  ⚠️  XML分析异常: {e}")
        
        return None
    
    async def _cursor_ai_vision_recognize(self, element_desc: str) -> Optional[Dict]:
        """
        Cursor AI视觉识别
        
        使用现有的视觉识别功能
        """
        try:
            from mobile_mcp.core.locator.cursor_vision_helper import CursorVisionHelper
            
            if hasattr(self, 'mobile_client') and self.mobile_client:
                cursor_helper = CursorVisionHelper(self.mobile_client)
                script_path = getattr(self, 'script_path', None)
                result = await cursor_helper.analyze_with_cursor(
                    element_desc,
                    script_path=script_path,
                    auto_analyze=True
                )
                
                if result and result.get('status') == 'completed':
                    coord = result.get('coordinate')
                    if coord:
                        return {
                            'coordinate': coord,
                            'screenshot_path': result.get('screenshot_path'),
                            'confidence': coord.get('confidence', 80)
                        }
        except Exception as e:
            print(f"  ⚠️  视觉识别异常: {e}")
            import traceback
            traceback.print_exc()
        
        return None
    
    async def execute(self, nl_text: str) -> Dict:
        """
        执行自然语言测试
        
        Args:
            nl_text: 自然语言测试描述
        
        Returns:
            执行结果
        """
        print("=" * 60)
        print("🚀 自然语言测试执行器")
        print("=" * 60)
        print(f"\n📝 输入: {nl_text}\n")
        
        # 解析自然语言
        steps = self.parse_natural_language(nl_text)
        print(f"✅ 解析完成，共 {len(steps)} 个步骤\n")
        
        # 执行步骤
        success_count = 0
        fail_count = 0
        
        for i, step in enumerate(steps):
            result = await self.execute_step(step, i)
            
            if result['success']:
                success_count += 1
            else:
                fail_count += 1
                # 可以选择是否继续执行
                # break
        
        # 生成Python模板
        python_code = self.generate_python_template()
        
        return {
            'total_steps': len(steps),
            'success_count': success_count,
            'fail_count': fail_count,
            'execution_log': self.execution_log,
            'python_template': python_code
        }
    
    def generate_python_template(self) -> str:
        """
        生成Python测试模板
        
        基于执行日志生成可复用的测试代码
        """
        lines = [
            "#!/usr/bin/env python3",
            "# -*- coding: utf-8 -*-",
            '"""',
            "自动生成的测试用例",
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            '"""',
            "import asyncio",
            "import sys",
            "from pathlib import Path",
            "",
            "sys.path.insert(0, str(Path(__file__).parent.parent.parent))",
            "from mobile_mcp.core.mobile_client import MobileClient",
            "from mobile_mcp.core.locator.mobile_smart_locator import MobileSmartLocator",
            "",
            "",
            "async def main():",
            "    client = MobileClient()",
            "    locator = MobileSmartLocator(client)",
            "",
        ]
        
        # 添加步骤
        for i, log in enumerate(self.execution_log):
            action = log['action']
            original_text = log.get('original_text', '')
            
            if action == 'launch_app':
                package = log.get('package', '')
                lines.append(f"    # 步骤 {i+1}: {original_text}")
                lines.append(f"    await client.launch_app('{package}', wait_time=3)")
                lines.append(f"    await asyncio.sleep(1)")
                lines.append("")
            
            elif action == 'click':
                element = log.get('element', '')
                method = log.get('method', '')
                element_ref = log.get('element_ref')
                coordinate = log.get('coordinate')
                
                lines.append(f"    # 步骤 {i+1}: {original_text}")
                lines.append(f"    # 定位方法: {method}")
                
                if coordinate:
                    x, y = coordinate['x'], coordinate['y']
                    lines.append(f"    # Cursor AI坐标: ({x}, {y})")
                    lines.append(f"    client.u2.click({x}, {y})")
                elif element_ref:
                    lines.append(f"    result = await locator.locate('{element}')")
                    lines.append(f"    if result:")
                    lines.append(f"        await client.click('{element}', ref=result['ref'])")
                else:
                    lines.append(f"    result = await locator.locate('{element}')")
                    lines.append(f"    if result:")
                    lines.append(f"        await client.click('{element}', ref=result['ref'])")
                
                lines.append(f"    await asyncio.sleep(0.5)")
                lines.append("")
            
            elif action == 'input':
                element = log.get('element', '')
                text = log.get('text', '')
                lines.append(f"    # 步骤 {i+1}: {original_text}")
                lines.append(f"    result = await locator.locate('{element}')")
                lines.append(f"    if result:")
                lines.append(f"        await client.type_text('{element}', '{text}', ref=result['ref'])")
                lines.append("")
            
            elif action == 'swipe':
                direction = log.get('direction', '')
                lines.append(f"    # 步骤 {i+1}: {original_text}")
                lines.append(f"    await client.swipe('{direction}')")
                lines.append("")
            
            elif action == 'wait':
                seconds = log.get('seconds', 1)
                lines.append(f"    # 步骤 {i+1}: {original_text}")
                lines.append(f"    await asyncio.sleep({seconds})")
                lines.append("")
            
            elif action == 'assert_text':
                text = log.get('text', '')
                lines.append(f"    # 步骤 {i+1}: {original_text}")
                lines.append(f"    snapshot = await client.snapshot()")
                lines.append(f"    assert '{text}' in snapshot, f\"未找到文本: {text}\"")
                lines.append("")
        
        lines.extend([
            "    client.device_manager.disconnect()",
            "",
            "",
            "if __name__ == \"__main__\":",
            "    asyncio.run(main())",
        ])
        
        return '\n'.join(lines)


async def main():
    """测试主函数"""
    # 这里需要传入MCP工具
    # 实际使用时，应该从MCP Server获取工具
    
    runner = NLTestRunner()
    
    # 测试自然语言
    nl_text = """
    启动应用com.im30.way，点击底部第四个图标，点击设置，点击语言，点击English，点击保存
    """
    
    result = await runner.execute(nl_text)
    
    print("\n" + "=" * 60)
    print("📊 执行总结")
    print("=" * 60)
    print(f"总步骤数: {result['total_steps']}")
    print(f"成功: {result['success_count']}")
    print(f"失败: {result['fail_count']}")
    print("\n" + "=" * 60)
    print("📝 生成的Python模板:")
    print("=" * 60)
    print(result['python_template'])


if __name__ == "__main__":
    asyncio.run(main())

