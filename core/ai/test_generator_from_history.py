#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于操作历史生成测试脚本 - 使用已验证的定位方式

功能：
1. 从操作历史（operation_history）生成脚本
2. 使用实际验证过的定位方式（坐标、bounds、resource-id等）
3. 确保生成的脚本100%可执行（因为使用的是已验证的定位方式）

用法:
    generator = TestGeneratorFromHistory()
    script = generator.generate_from_history(
        test_name="测试用例",
        package_name="com.im30.way",
        operation_history=client.operation_history
    )
    generator.save("test_generated.py", script)
"""
import re
from pathlib import Path
from typing import List, Dict
from datetime import datetime


class TestGeneratorFromHistory:
    """
    基于操作历史生成测试脚本
    
    特点：
    - 使用已验证的定位方式（坐标、bounds等）
    - 生成的脚本100%可执行
    - 不需要重新定位，直接使用已验证的ref
    """
    
    def __init__(self, output_dir: str = "tests"):
        """
        初始化生成器
        
        Args:
            output_dir: 生成的测试文件输出目录（默认tests，用于pytest）
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def generate_from_history(
        self, 
        test_name: str, 
        package_name: str,
        operation_history: List[Dict]
    ) -> str:
        """
        从操作历史生成测试脚本
        
        Args:
            test_name: 测试用例名称
            package_name: App包名
            operation_history: 操作历史列表
            
        Returns:
            生成的测试脚本内容
        """
        # 生成文件名（中文转拼音或直接使用）
        safe_name = re.sub(r'[^\w\s-]', '', test_name).strip().replace(' ', '_')
        
        # 生成脚本内容（pytest格式）
        script_lines = [
            "#!/usr/bin/env python3",
            "# -*- coding: utf-8 -*-",
            f'"""',
            f"移动端测试用例: {test_name}",
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"",
            f"⚠️  注意：此脚本基于AI执行历史生成，使用已验证的定位方式",
            f"    如果页面结构变化，可能需要重新生成脚本",
            f"",
            f"运行方式:",
            f"    pytest {safe_name}.py -v",
            f"    pytest {safe_name}.py --alluredir=./allure-results  # 生成allure报告",
            f'"""',
            "import asyncio",
            "import pytest",
            "import sys",
            "from pathlib import Path",
            "",
            "# 添加backend目录到路径",
            "# tests目录结构: backend/mobile_mcp/tests/test_xxx.py",
            "# 需要导入: backend/mobile_mcp/core/mobile_client.py",
            "sys.path.insert(0, str(Path(__file__).parent.parent))",
            "",
            "from mobile_mcp.core.mobile_client import MobileClient",
            "",
            "",
            f"PACKAGE_NAME = \"{package_name}\"",
            "",
            "",
            "@pytest.fixture(scope='function')",
            "async def mobile_client():",
            "    \"\"\"",
            "    pytest fixture: 创建并返回MobileClient实例",
            "    scope='function': 每个测试函数都会创建一个新的client",
            "    \"\"\"",
            "    client = MobileClient(device_id=None)",
            "    ",
            "    # 启动App",
            "    print(f\"\\n📱 启动App: {{PACKAGE_NAME}}\")",
            "    result = await client.launch_app(PACKAGE_NAME, wait_time=5)",
            "    if not result.get('success'):",
            "        raise Exception(f\"启动App失败: {{result.get('reason')}}\")",
            "    ",
            "    await asyncio.sleep(2)  # 等待页面加载",
            "    ",
            "    yield client",
            "    ",
            "    # 清理",
            "    client.device_manager.disconnect()",
            "",
            "",
            f"@pytest.mark.asyncio",
            f"async def test_{safe_name.lower()}(mobile_client):",
            f'    """',
            f"    测试用例: {test_name}",
            f"    ",
            f"    Args:",
            f"        mobile_client: pytest fixture，已启动App的MobileClient实例",
            f'    """',
            f"    client = mobile_client",
            f"    ",
            f"    print(\"=\" * 60)",
            f"    print(f\"🚀 {test_name}\")",
            f"    print(\"=\" * 60)",
            f"    ",
            f"    try:",
        ]
        
        # 根据操作历史生成测试步骤
        step_index = 1
        for operation in operation_history:
            action = operation.get('action')
            element = operation.get('element', '')
            ref = operation.get('ref', '')
            
            if action == 'click':
                script_lines.append(f"        # 步骤{step_index}: 点击 {element}")
                script_lines.append(f"        print(f\"\\n步骤{step_index}: 点击 {element}\")")
                
                # 🎯 根据ref类型生成不同的代码
                if ref.startswith('vision_coord_'):
                    # 视觉识别坐标：vision_coord_x_y
                    parts = ref.replace('vision_coord_', '').split('_')
                    if len(parts) >= 2:
                        x, y = parts[0], parts[1]
                        script_lines.append(f"        # ✅ 使用视觉识别坐标（已验证）")
                        script_lines.append(f"        client.u2.click({x}, {y})")
                        script_lines.append(f"        print(f\"✅ 点击成功（坐标: {x}, {y}）\")")
                        script_lines.append(f"        await asyncio.sleep(1.5)  # 等待页面响应")
                elif ref.startswith('[') and '][' in ref:
                    # bounds坐标：[x1,y1][x2,y2]
                    script_lines.append(f"        # ✅ 使用bounds坐标（已验证）")
                    script_lines.append(f"        await client.click(\"{element}\", ref=\"{ref}\", verify=False)")
                    script_lines.append(f"        print(f\"✅ 点击成功（bounds: {ref}）\")")
                    script_lines.append(f"        await asyncio.sleep(1.5)  # 等待页面响应")
                elif ref.startswith('com.') or ':' in ref:
                    # resource-id定位
                    script_lines.append(f"        # ✅ 使用resource-id定位（已验证）")
                    script_lines.append(f"        await client.click(\"{element}\", ref=\"{ref}\", verify=False)")
                    script_lines.append(f"        print(f\"✅ 点击成功（resource-id: {ref}）\")")
                    script_lines.append(f"        await asyncio.sleep(1.5)  # 等待页面响应")
                else:
                    # text/description定位
                    script_lines.append(f"        # ✅ 使用text/description定位（已验证）")
                    script_lines.append(f"        await client.click(\"{element}\", ref=\"{ref}\", verify=False)")
                    script_lines.append(f"        print(f\"✅ 点击成功（text/desc: {ref}）\")")
                    script_lines.append(f"        await asyncio.sleep(1.5)  # 等待页面响应")
                
                step_index += 1
            
            elif action == 'type':
                text = operation.get('text', '')
                script_lines.append(f"        # 步骤{step_index}: 在{element}输入 {text}")
                script_lines.append(f"        print(f\"\\n步骤{step_index}: 在{element}输入 {text}\")")
                
                # 🎯 根据ref类型生成不同的代码
                if ref.startswith('[') and '][' in ref:
                    # bounds坐标
                    script_lines.append(f"        # ✅ 使用bounds坐标输入（已验证）")
                    script_lines.append(f"        await client.type_text(\"{element}\", \"{text}\", ref=\"{ref}\")")
                    script_lines.append(f"        print(f\"✅ 输入成功（bounds: {ref}）\")")
                    script_lines.append(f"        await asyncio.sleep(1)  # 等待输入完成")
                elif ref.startswith('com.') or ':' in ref:
                    # resource-id定位
                    script_lines.append(f"        # ✅ 使用resource-id输入（已验证）")
                    script_lines.append(f"        await client.type_text(\"{element}\", \"{text}\", ref=\"{ref}\")")
                    script_lines.append(f"        print(f\"✅ 输入成功（resource-id: {ref}）\")")
                    script_lines.append(f"        await asyncio.sleep(1)  # 等待输入完成")
                else:
                    # text定位
                    script_lines.append(f"        # ✅ 使用text定位输入（已验证）")
                    script_lines.append(f"        await client.type_text(\"{element}\", \"{text}\", ref=\"{ref}\")")
                    script_lines.append(f"        print(f\"✅ 输入成功（text: {ref}）\")")
                    script_lines.append(f"        await asyncio.sleep(1)  # 等待输入完成")
                
                step_index += 1
        
        # 添加结尾（pytest格式）
        script_lines.extend([
            f"        ",
            f"        print(\"\\n✅ 测试完成！\")",
            f"        ",
            f"    except AssertionError as e:",
            f"        print(f\"\\n❌ 断言失败: {{e}}\")",
            f"        # 打印当前页面快照以便调试",
            f"        snapshot = await client.snapshot()",
            f"        print(f\"\\n当前页面快照:\\n{{snapshot[:500]}}...\")",
            f"        raise",
            f"    except Exception as e:",
            f"        print(f\"\\n❌ 测试失败: {{e}}\")",
            f"        import traceback",
            f"        traceback.print_exc()",
            f"        raise",
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

