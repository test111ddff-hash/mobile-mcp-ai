#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
移动端测试用例生成器
自然语言 → 移动端测试脚本

用法:
    generator = MobileTestGenerator()
    script = generator.generate("打开App\n点击登录按钮\n输入邮箱 test@example.com")
    generator.save("test_login.py", script)
"""
import re
from pathlib import Path
from typing import List, Dict
from datetime import datetime


class MobileTestStep:
    """移动端测试步骤"""
    def __init__(self, action: str, **kwargs):
        self.action = action
        self.params = kwargs
    
    def __repr__(self):
        return f"MobileTestStep(action={self.action}, params={self.params})"


class MobileTestGenerator:
    """
    移动端测试用例生成器
    
    功能：
    1. 解析自然语言测试用例
    2. 生成移动端测试脚本
    3. 支持中文自然语言输入
    """
    
    def __init__(self, output_dir: str = "tests"):
        """
        初始化生成器
        
        Args:
            output_dir: 生成的测试文件输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def parse_natural_language(self, test_case: str) -> List[MobileTestStep]:
        """
        解析自然语言测试用例
        
        Args:
            test_case: 自然语言描述的测试用例（中文）
            
        Returns:
            测试步骤列表
        """
        steps = []
        lines = [line.strip() for line in test_case.strip().split('\n') if line.strip()]
        
        for line in lines:
            # 跳过注释
            if line.startswith('#'):
                continue
            
            # 解析打开App
            if "打开App" in line or "启动App" in line:
                # 提取包名（如果有）
                package_match = re.search(r'(?:打开|启动)(?:App|应用)[：:]\s*([^\s]+)', line)
                package = package_match.group(1) if package_match else None
                steps.append(MobileTestStep('launch_app', package=package, raw=line))
            
            # 解析点击
            elif "点击" in line:
                description = line.replace("点击", "").strip()
                # 自动识别常见模式
                # "点击底部导航栏第3个图标" → description="底部导航栏第3个图标"
                # "点击右下角加号" → description="右下角加号"
                # "点击登录" → description="登录"
                steps.append(MobileTestStep(
                    'click',
                    description=description,
                    raw=line
                ))
            
            # 解析输入
            elif "输入" in line:
                # 支持多种格式：
                # "在邮箱输入框输入 test@example.com"
                # "邮箱输入框输入 test@example.com"
                # "输入邮箱 test@example.com"
                # "输入密码 password123"
                # "内容输入框输入 自动化测试"
                
                input_match = re.search(r'(.+?)输入\s+(.+)', line)
                if input_match:
                    field_desc = input_match.group(1).strip()
                    text_content = input_match.group(2).strip()
                    
                    # 清理描述
                    clean_desc = field_desc.replace("在", "").replace("的", "").strip()
                    
                    # 智能补全"输入框"后缀
                    if "输入框" not in clean_desc:
                        # 如果只是关键词（如"邮箱"、"密码"、"内容"），自动补全
                        if clean_desc and not any(kw in clean_desc for kw in ["按钮", "图标", "标签"]):
                            clean_desc = f"{clean_desc}输入框"
                        elif not clean_desc:
                            clean_desc = "输入框"
                    
                    steps.append(MobileTestStep(
                        'type',
                        description=clean_desc,
                        text=text_content,
                        raw=line
                    ))
            
            # 解析滑动
            elif "滑动" in line or "滑动" in line:
                direction_match = re.search(r'(?:向上|向下|向左|向右|上|下|左|右)', line)
                if direction_match:
                    direction_text = direction_match.group(0)
                    direction_map = {
                        '向上': 'up', '上': 'up',
                        '向下': 'down', '下': 'down',
                        '向左': 'left', '左': 'left',
                        '向右': 'right', '右': 'right'
                    }
                    direction = direction_map.get(direction_text, 'up')
                    steps.append(MobileTestStep('swipe', direction=direction, raw=line))
            
            # 解析等待
            elif "等待" in line:
                time_match = re.search(r'(\d+)', line)
                if time_match:
                    steps.append(MobileTestStep('wait', seconds=int(time_match.group(1)), raw=line))
            
            # 解析断言
            elif "断言" in line or "检查" in line:
                description = line.replace("断言", "").replace("检查", "").strip()
                steps.append(MobileTestStep('assert', description=description, raw=line))
        
        return steps
    
    def generate_test_script(self, test_name: str, test_case: str, package_name: str = "com.im30.way") -> str:
        """
        生成移动端测试脚本
        
        Args:
            test_name: 测试用例名称（中文，会自动转换为文件名）
            test_case: 自然语言测试用例
            package_name: App包名
            
        Returns:
            生成的测试脚本内容
        """
        steps = self.parse_natural_language(test_case)
        
        # 生成文件名（中文转拼音或直接使用）
        safe_name = re.sub(r'[^\w\s-]', '', test_name).strip().replace(' ', '_')
        
        # 生成脚本内容
        script_lines = [
            "#!/usr/bin/env python3",
            "# -*- coding: utf-8 -*-",
            f'"""',
            f"移动端测试用例: {test_name}",
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"",
            f"原始测试用例:",
            *[f"{step.params.get('raw', '')}" for step in steps if step.params.get('raw')],
            f'"""',
            "import asyncio",
            "import sys",
            "from pathlib import Path",
            "",
            "# 添加backend目录到路径",
            "sys.path.insert(0, str(Path(__file__).parent.parent.parent))",
            "",
            "from mobile_mcp.core.mobile_client import MobileClient",
            "from mobile_mcp.core.locator.mobile_smart_locator import MobileSmartLocator",
            "",
            "",
            f"class Test{safe_name}:",
            f'    """测试类: {test_name}"""',
            f"    ",
            f"    PACKAGE_NAME = \"{package_name}\"",
            f"    ",
            f"    def __init__(self):",
            f"        self.client = None",
            f"        self.locator = None",
            f"    ",
            f"    async def setup(self):",
            f"        \"\"\"测试前置准备\"\"\"",
            f"        print(\"=\" * 60)",
            f"        print(f\"🚀 {test_name}\")",
            f"        print(\"=\" * 60)",
            f"        ",
            f"        # 连接设备",
            f"        print(\"\\n📱 连接设备...\")",
            f"        self.client = MobileClient(device_id=None)",
            f"        self.locator = MobileSmartLocator(self.client)",
            f"        ",
            f"        # 启动App",
            f"        print(f\"\\n📱 启动App: {{self.PACKAGE_NAME}}\")",
            f"        result = await self.client.launch_app(self.PACKAGE_NAME, wait_time=5)",
            f"        if not result.get('success'):",
            f"            raise Exception(f\"启动App失败: {{result.get('reason')}}\")",
            f"        ",
            f"        await asyncio.sleep(2)  # 等待页面加载",
            f"    ",
            f"    async def teardown(self):",
            f"        \"\"\"测试后清理\"\"\"",
            f"        if self.client:",
            f"            self.client.device_manager.disconnect()",
            f"    ",
            f"    async def test_case(self):",
            f"        \"\"\"测试用例主体\"\"\"",
            f"        try:",
        ]
        
        # 生成测试步骤代码
        step_index = 1
        for step in steps:
            action = step.action
            params = step.params
            
            if action == 'launch_app':
                if params.get('package'):
                    script_lines.append(f"            # 步骤{step_index}: {params.get('raw', '启动App')}")
                    script_lines.append(f"            result = await self.client.launch_app(\"{params['package']}\", wait_time=5)")
                    script_lines.append(f"            await asyncio.sleep(2)")
                else:
                    script_lines.append(f"            # 步骤{step_index}: {params.get('raw', '启动App')}")
                    script_lines.append(f"            # App已在setup中启动")
            
            elif action == 'click':
                description = params.get('description', '')
                script_lines.append(f"            # 步骤{step_index}: {params.get('raw', f'点击{description}')}")
                script_lines.append(f"            print(f\"\\n步骤{step_index}: 点击 {description}\")")
                script_lines.append(f"            result = await self.locator.locate(\"{description}\")")
                script_lines.append(f"            if result:")
                script_lines.append(f"                click_result = await self.client.click(\"{description}\", ref=result['ref'])")
                script_lines.append(f"                if click_result.get('success'):")
                script_lines.append(f"                    print(f\"✅ 点击成功\")")
                script_lines.append(f"                    await asyncio.sleep(1)")
                script_lines.append(f"                else:")
                script_lines.append(f"                    print(f\"⚠️  点击失败: {{click_result.get('reason')}}\")")
                script_lines.append(f"                    # 尝试使用坐标点击（如果ref包含坐标信息）")
                script_lines.append(f"                    ref = result.get('ref', '')")
                script_lines.append(f"                    if ref.startswith('vision_coord_') or (ref.startswith('[') and '][' in ref):")
                script_lines.append(f"                        print(f\"  尝试使用坐标点击: {{ref}}\")")
                script_lines.append(f"                        await self.client.click(\"{description}\", ref=ref, verify=False)")
                script_lines.append(f"                        await asyncio.sleep(1)")
                script_lines.append(f"            else:")
                script_lines.append(f"                print(f\"⚠️  未找到: {description}，尝试视觉识别...\")")
                script_lines.append(f"                # 🎯 定位失败时，尝试视觉识别获取坐标")
                script_lines.append(f"                try:")
                script_lines.append(f"                    from mobile_mcp.vision.vision_locator import MobileVisionLocator")
                script_lines.append(f"                    vision_locator = MobileVisionLocator(self.client)")
                script_lines.append(f"                    vision_result = await vision_locator.locate_element_by_vision(\"{description}\")")
                script_lines.append(f"                    if vision_result and vision_result.get('found'):")
                script_lines.append(f"                        x = vision_result.get('x', 0)")
                script_lines.append(f"                        y = vision_result.get('y', 0)")
                script_lines.append(f"                        print(f\"  ✅ 视觉识别成功，坐标: ({{x}}, {{y}})\")")
                script_lines.append(f"                        self.client.u2.click(x, y)")
                script_lines.append(f"                        await asyncio.sleep(1)")
                script_lines.append(f"                    else:")
                script_lines.append(f"                        print(f\"  ❌ 视觉识别也失败: {{vision_result.get('reason', 'unknown') if vision_result else 'unknown'}}\")")
                script_lines.append(f"                        raise Exception(f\"无法定位元素: {description}\")")
                script_lines.append(f"                except Exception as e:")
                script_lines.append(f"                    print(f\"  ❌ 视觉识别异常: {{e}}\")")
                script_lines.append(f"                    raise Exception(f\"无法定位元素: {description}\")")
            
            elif action == 'type':
                description = params.get('description', '输入框')
                text = params.get('text', '')
                script_lines.append(f"            # 步骤{step_index}: {params.get('raw', f'输入{text}')}")
                script_lines.append(f"            print(f\"\\n步骤{step_index}: 在{description}输入 {text}\")")
                script_lines.append(f"            result = await self.locator.locate(\"{description}\")")
                script_lines.append(f"            if result:")
                script_lines.append(f"                await self.client.type_text(\"{description}\", \"{text}\", ref=result['ref'])")
                script_lines.append(f"                await asyncio.sleep(0.5)")
                script_lines.append(f"            else:")
                script_lines.append(f"                print(f\"⚠️  未找到: {description}\")")
            
            elif action == 'swipe':
                direction = params.get('direction', 'up')
                script_lines.append(f"            # 步骤{step_index}: {params.get('raw', f'滑动{direction}')}")
                script_lines.append(f"            print(f\"\\n步骤{step_index}: 滑动 {direction}\")")
                script_lines.append(f"            await self.client.swipe(\"{direction}\")")
                script_lines.append(f"            await asyncio.sleep(1)")
            
            elif action == 'wait':
                seconds = params.get('seconds', 1)
                script_lines.append(f"            # 步骤{step_index}: {params.get('raw', f'等待{seconds}秒')}")
                script_lines.append(f"            await asyncio.sleep({seconds})")
            
            elif action == 'assert':
                description = params.get('description', '')
                script_lines.append(f"            # 步骤{step_index}: {params.get('raw', f'断言{description}')}")
                script_lines.append(f"            print(f\"\\n步骤{step_index}: 验证 {description}\")")
                script_lines.append(f"            snapshot = await self.client.snapshot()")
                script_lines.append(f"            if \"{description}\" in snapshot:")
                script_lines.append(f"                print(f\"✅ 验证通过: {description}\")")
                script_lines.append(f"            else:")
                script_lines.append(f"                print(f\"⚠️  验证失败: {description}\")")
            
            step_index += 1
        
        # 添加结尾
        script_lines.extend([
            f"            ",
            f"            # 打印统计信息",
            f"            print(\"\\n\" + \"=\" * 60)",
            f"            print(\"📊 定位统计:\")",
            f"            print(\"=\" * 60)",
            f"            print(f\"  总定位次数: {{self.locator.stats['total']}}\")",
            f"            print(f\"  规则匹配: {{self.locator.stats['rule_hits']}}\")",
            f"            print(f\"  缓存命中: {{self.locator.stats['cache_hits']}}\")",
            f"            print(f\"  XML分析: {{self.locator.stats['xml_analysis']}}\")",
            f"            print(f\"  视觉识别: {{self.locator.stats['vision_calls']}}\")",
            f"            print(f\"  AI分析: {{self.locator.stats['ai_calls']}}\")",
            f"            ",
            f"            print(\"\\n✅ 测试完成！\")",
            f"            ",
            f"        except Exception as e:",
            f"            print(f\"\\n❌ 测试失败: {{e}}\")",
            f"            import traceback",
            f"            traceback.print_exc()",
            f"            raise",
            f"",
            f"",
            f"async def run_test():",
            f"    \"\"\"运行测试\"\"\"",
            f"    test = Test{safe_name}()",
            f"    try:",
            f"        await test.setup()",
            f"        await test.test_case()",
            f"    finally:",
            f"        await test.teardown()",
            f"",
            f"",
            f"if __name__ == \"__main__\":",
            f"    asyncio.run(run_test())",
        ])
        
        return '\n'.join(script_lines)
    
    def save(self, filename: str, script: str):
        """
        保存生成的测试脚本
        
        Args:
            filename: 文件名（会自动添加.py后缀）
            script: 脚本内容
        """
        if not filename.endswith('.py'):
            filename += '.py'
        
        file_path = self.output_dir / filename
        file_path.write_text(script, encoding='utf-8')
        print(f"✅ 测试用例已保存: {file_path}")
        return file_path

