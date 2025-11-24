#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能测试执行器 - 让Cursor AI自动规划、执行、验证和解决问题

功能：
1. 解析自然语言测试用例
2. 自动执行每一步操作
3. 每一步后自动验证是否成功（通过页面元素变化）
4. 失败时自动分析问题并重试
5. 找不到元素时自动截图分析
6. 自动判断操作成功（页面元素出现/变化）
"""
import asyncio
import json
import time
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime

from ...core.mobile_client import MobileClient
from ...core.locator.mobile_smart_locator import MobileSmartLocator


class SmartTestExecutor:
    """
    智能测试执行器
    
    让Cursor AI自动规划、执行、验证和解决问题
    """
    
    def __init__(self, client: Optional[MobileClient] = None, locator: Optional[MobileSmartLocator] = None):
        """
        初始化智能测试执行器
        
        Args:
            client: MobileClient实例（可选，会自动创建）
            locator: MobileSmartLocator实例（可选，会自动创建）
        """
        self.client = client or MobileClient()
        self.locator = locator or MobileSmartLocator(self.client)
        
        # 执行历史
        self.execution_history: List[Dict] = []
        
        # 页面状态快照（用于对比变化）
        self.last_snapshot: Optional[str] = None
        self.last_snapshot_time: float = 0
    
    async def parse_test_case(self, test_description: str) -> List[Dict]:
        """
        解析自然语言测试用例
        
        Args:
            test_description: 自然语言描述的测试用例
            
        Returns:
            步骤列表
        """
        steps = []
        
        # 简单的规则解析（可以后续用AI增强）
        lines = test_description.strip().split('\n')
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # 移除序号（如 "1. "、"步骤1："等）
            import re
            line = re.sub(r'^\d+[\.、]\s*', '', line)
            line = re.sub(r'^步骤\d+[：:]\s*', '', line)
            
            # 解析操作类型
            if '打开' in line or '启动' in line:
                # 提取包名
                package_match = re.search(r'com\.\w+(?:\.\w+)*', line)
                if package_match:
                    steps.append({
                        'step_num': i,
                        'action': 'launch_app',
                        'description': line,
                        'package': package_match.group(),
                        'wait_time': 3
                    })
            elif '点击' in line:
                # 提取元素描述
                element = line.replace('点击', '').strip()
                steps.append({
                    'step_num': i,
                    'action': 'click',
                    'description': line,
                    'element': element,
                    'verify': True  # 默认验证
                })
            elif '输入' in line:
                # 提取输入框和文本
                input_match = re.search(r'输入(.+?)(?:为|：|:)(.+)', line)
                if input_match:
                    element = input_match.group(1).strip()
                    text = input_match.group(2).strip()
                    steps.append({
                        'step_num': i,
                        'action': 'input',
                        'description': line,
                        'element': element,
                        'text': text,
                        'verify': True
                    })
            elif '等待' in line:
                # 提取等待时间
                wait_match = re.search(r'(\d+)', line)
                if wait_match:
                    seconds = int(wait_match.group(1))
                    steps.append({
                        'step_num': i,
                        'action': 'wait',
                        'description': line,
                        'seconds': seconds
                    })
            elif '验证' in line or '检查' in line or '断言' in line:
                # 提取验证文本
                text_match = re.search(r'["\'](.+?)["\']', line)
                if text_match:
                    text = text_match.group(1)
                    steps.append({
                        'step_num': i,
                        'action': 'verify',
                        'description': line,
                        'expected_text': text
                    })
        
        return steps
    
    async def get_page_snapshot(self) -> str:
        """获取当前页面快照"""
        snapshot = await self.client.snapshot()
        self.last_snapshot = snapshot
        self.last_snapshot_time = time.time()
        return snapshot
    
    async def verify_page_change(self, expected_elements: List[str] = None, 
                                 unexpected_elements: List[str] = None,
                                 min_wait: float = 0.5) -> Dict:
        """
        验证页面是否发生变化
        
        Args:
            expected_elements: 期望出现的元素列表
            unexpected_elements: 期望消失的元素列表
            min_wait: 最小等待时间（秒）
            
        Returns:
            验证结果
        """
        # 等待页面响应
        await asyncio.sleep(min_wait)
        
        # 获取新快照
        new_snapshot = await self.get_page_snapshot()
        
        result = {
            'success': True,
            'page_changed': new_snapshot != self.last_snapshot if self.last_snapshot else True,
            'expected_found': [],
            'expected_missing': [],
            'unexpected_found': [],
            'unexpected_missing': []
        }
        
        # 检查期望出现的元素
        if expected_elements:
            for elem in expected_elements:
                if elem in new_snapshot:
                    result['expected_found'].append(elem)
                else:
                    result['expected_missing'].append(elem)
                    result['success'] = False
        
        # 检查期望消失的元素
        if unexpected_elements:
            for elem in unexpected_elements:
                if elem not in new_snapshot:
                    result['unexpected_missing'].append(elem)
                else:
                    result['unexpected_found'].append(elem)
                    result['success'] = False
        
        return result
    
    async def execute_click_with_verification(self, element_desc: str, 
                                            expected_after: List[str] = None,
                                            unexpected_after: List[str] = None,
                                            max_retries: int = 2) -> Dict:
        """
        执行点击操作并自动验证
        
        Args:
            element_desc: 元素描述
            expected_after: 点击后期望出现的元素
            unexpected_after: 点击后期望消失的元素
            max_retries: 最大重试次数
            
        Returns:
            执行结果
        """
        result = {
            'success': False,
            'element': element_desc,
            'method': None,
            'retries': 0,
            'error': None
        }
        
        # 获取点击前的快照
        snapshot_before = await self.get_page_snapshot()
        
        for attempt in range(max_retries + 1):
            result['retries'] = attempt + 1
            
            try:
                # 定位元素
                print(f"\n  🔍 尝试定位: {element_desc} (第{attempt + 1}次)")
                locate_result = await self.locator.locate(element_desc)
                
                if not locate_result:
                    # 定位失败，截图分析
                    print(f"  ⚠️  定位失败，截图分析...")
                    screenshot_path = await self._take_screenshot_for_analysis(element_desc)
                    result['error'] = f"未找到元素: {element_desc}"
                    result['screenshot_path'] = screenshot_path
                    
                    if attempt < max_retries:
                        print(f"  ⏳ 等待1秒后重试...")
                        await asyncio.sleep(1)
                        continue
                    else:
                        return result
                
                # 执行点击
                ref = locate_result.get('ref', '')
                method = locate_result.get('method', 'unknown')
                result['method'] = method
                
                print(f"  ✅ 定位成功: {method}")
                print(f"  🖱️  执行点击...")
                
                click_result = await self.client.click(element_desc, ref=ref, verify=False)
                
                if not click_result.get('success'):
                    result['error'] = click_result.get('reason', '点击失败')
                    if attempt < max_retries:
                        await asyncio.sleep(1)
                        continue
                    return result
                
                # 验证点击是否成功（通过页面变化）
                print(f"  🔍 验证点击是否成功...")
                await asyncio.sleep(0.5)  # 等待页面响应
                
                verification = await self.verify_page_change(
                    expected_elements=expected_after,
                    unexpected_elements=unexpected_after
                )
                
                if verification['page_changed']:
                    print(f"  ✅ 页面已变化，点击可能成功")
                    result['success'] = True
                    
                    # 如果有期望元素，检查是否出现
                    if expected_after:
                        if verification['expected_found']:
                            print(f"  ✅ 期望元素已出现: {verification['expected_found']}")
                        if verification['expected_missing']:
                            print(f"  ⚠️  期望元素未出现: {verification['expected_missing']}")
                    
                    return result
                else:
                    print(f"  ⚠️  页面未变化，点击可能失败")
                    if attempt < max_retries:
                        print(f"  🔄 重试点击...")
                        await asyncio.sleep(1)
                        continue
                    else:
                        result['error'] = "点击后页面未变化"
                        return result
                        
            except Exception as e:
                result['error'] = str(e)
                print(f"  ❌ 执行异常: {e}")
                if attempt < max_retries:
                    await asyncio.sleep(1)
                    continue
                return result
        
        return result
    
    async def _take_screenshot_for_analysis(self, element_desc: str) -> str:
        """截图用于分析"""
        from datetime import datetime
        screenshot_dir = Path(__file__).parent.parent.parent.parent / "screenshots"
        screenshot_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = screenshot_dir / f"screenshot_{element_desc}_{timestamp}.png"
        
        self.client.u2.screenshot(str(screenshot_path))
        print(f"  📸 截图已保存: {screenshot_path}")
        
        return str(screenshot_path)
    
    async def execute_step(self, step: Dict) -> Dict:
        """
        执行单个步骤
        
        Args:
            step: 步骤信息
            
        Returns:
            执行结果
        """
        step_num = step.get('step_num', 0)
        action = step.get('action')
        description = step.get('description', '')
        
        print(f"\n{'='*60}")
        print(f"📋 步骤 {step_num}: {description}")
        print(f"{'='*60}")
        
        result = {
            'step_num': step_num,
            'action': action,
            'description': description,
            'success': False,
            'timestamp': datetime.now().isoformat(),
            'details': {}
        }
        
        try:
            if action == 'launch_app':
                package = step.get('package')
                wait_time = step.get('wait_time', 3)
                
                print(f"  🚀 启动应用: {package}")
                await self.client.launch_app(package, wait_time=wait_time)
                
                # 验证应用是否启动成功
                await asyncio.sleep(1)
                current_package = self.client.u2.app_current()['package']
                if current_package == package:
                    result['success'] = True
                    result['details'] = {'package': package}
                    print(f"  ✅ 应用启动成功")
                else:
                    result['details'] = {'expected': package, 'actual': current_package}
                    print(f"  ⚠️  应用可能未启动成功（当前: {current_package}）")
            
            elif action == 'click':
                element = step.get('element')
                verify = step.get('verify', True)
                
                # 根据步骤描述推断期望的变化
                expected_after = []
                unexpected_after = []
                
                # 简单的推断逻辑（可以后续用AI增强）
                if '云文档' in description and '底部' in description:
                    expected_after = ['云文档', '我的空间']
                elif '我的空间' in description:
                    expected_after = ['我的空间']
                elif '加号' in description or '新建' in description:
                    expected_after = ['云文档', '在线表格', '思维笔记']
                elif '删除' in description:
                    unexpected_after = ['删除']  # 删除后，删除按钮应该消失
                
                click_result = await self.execute_click_with_verification(
                    element,
                    expected_after=expected_after if verify else None,
                    unexpected_after=unexpected_after if verify else None
                )
                
                result['success'] = click_result['success']
                result['details'] = click_result
            
            elif action == 'input':
                element = step.get('element')
                text = step.get('text')
                
                print(f"  ⌨️  输入: {element} = {text}")
                
                # 定位输入框
                locate_result = await self.locator.locate(element)
                if not locate_result:
                    result['details'] = {'error': f"未找到输入框: {element}"}
                    return result
                
                # 执行输入
                input_result = await self.client.type_text(element, text, ref=locate_result['ref'])
                if input_result.get('success'):
                    result['success'] = True
                    result['details'] = {'element': element, 'text': text}
                    print(f"  ✅ 输入成功")
                else:
                    result['details'] = input_result
            
            elif action == 'wait':
                seconds = step.get('seconds', 1)
                print(f"  ⏳ 等待 {seconds}秒")
                await asyncio.sleep(seconds)
                result['success'] = True
            
            elif action == 'verify':
                expected_text = step.get('expected_text')
                print(f"  ✅ 验证: 检查文本 '{expected_text}'")
                
                snapshot = await self.get_page_snapshot()
                if expected_text in snapshot:
                    result['success'] = True
                    result['details'] = {'found': True}
                    print(f"  ✅ 验证成功: 找到文本 '{expected_text}'")
                else:
                    result['details'] = {'found': False}
                    print(f"  ❌ 验证失败: 未找到文本 '{expected_text}'")
            
        except Exception as e:
            result['details'] = {'error': str(e)}
            print(f"  ❌ 执行异常: {e}")
            import traceback
            traceback.print_exc()
        
        # 记录执行历史
        self.execution_history.append(result)
        
        return result
    
    async def execute_test_case(self, test_description: str) -> Dict:
        """
        执行完整的测试用例
        
        Args:
            test_description: 自然语言描述的测试用例
            
        Returns:
            执行结果
        """
        print("="*60)
        print("🚀 智能测试执行器")
        print("="*60)
        print(f"\n📝 测试用例:\n{test_description}\n")
        
        # 解析测试用例
        steps = await self.parse_test_case(test_description)
        print(f"✅ 解析完成，共 {len(steps)} 个步骤\n")
        
        # 执行步骤
        results = []
        success_count = 0
        fail_count = 0
        
        for step in steps:
            result = await self.execute_step(step)
            results.append(result)
            
            if result['success']:
                success_count += 1
            else:
                fail_count += 1
                # 可以选择是否继续执行
                # break
        
        # 生成报告
        report = {
            'total_steps': len(steps),
            'success_count': success_count,
            'fail_count': fail_count,
            'results': results,
            'execution_history': self.execution_history
        }
        
        print("\n" + "="*60)
        print("📊 执行报告")
        print("="*60)
        print(f"总步骤数: {report['total_steps']}")
        print(f"成功: {success_count}")
        print(f"失败: {fail_count}")
        print(f"成功率: {success_count/len(steps)*100:.1f}%")
        
        return report


async def main():
    """测试主函数"""
    executor = SmartTestExecutor()
    
    test_case = """
打开 com.im30.mind
点击底部云文档
点击我的空间
点击蓝色加号
点击云文档（新）
等待3秒
点击右上角三个点图标
弹出的弹窗内点击删除
之后会再有一个弹窗，点击删除
"""
    
    result = await executor.execute_test_case(test_case)
    
    # 保存报告
    report_path = Path(__file__).parent.parent.parent.parent / "test_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 报告已保存: {report_path}")


if __name__ == "__main__":
    asyncio.run(main())

