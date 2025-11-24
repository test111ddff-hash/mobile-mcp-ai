#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从操作历史生成测试脚本 - 确保100%可执行

功能：
1. 从 MobileClient 的操作历史生成测试脚本
2. 使用实际验证过的定位方式（坐标、bounds、resource-id等）
3. 确保生成的脚本100%可执行（因为使用的是已验证的定位方式）

用法:
    from mobile_mcp.core.mobile_client import MobileClient
    from mobile_mcp.core.ai.test_generator_from_history import TestGeneratorFromHistory
    
    client = MobileClient()
    # ... 执行操作 ...
    
    # 生成脚本
    generator = TestGeneratorFromHistory(output_dir="examples")
    script = generator.generate_from_history(
        test_name="建议发帖测试",
        package_name="com.im30.way",
        operation_history=client.operation_history
    )
    generator.save("test_generated.py", script)
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from mobile_mcp.core.mobile_client import MobileClient
from mobile_mcp.core.ai.test_generator_from_history import TestGeneratorFromHistory


def generate_script_from_client(
    client: MobileClient,
    test_name: str,
    package_name: str = "com.im30.way",
    output_dir: str = "examples"
):
    """
    从客户端操作历史生成测试脚本
    
    Args:
        client: MobileClient实例（包含operation_history）
        test_name: 测试用例名称
        package_name: App包名
        output_dir: 输出目录
    """
    generator = TestGeneratorFromHistory(output_dir=output_dir)
    
    # 只保留成功的操作
    successful_operations = [
        op for op in client.operation_history 
        if op.get('success', False)
    ]
    
    if not successful_operations:
        print("⚠️  没有成功的操作记录，无法生成脚本")
        return None
    
    print(f"📝 从 {len(successful_operations)} 个成功操作生成脚本...")
    
    script = generator.generate_from_history(
        test_name=test_name,
        package_name=package_name,
        operation_history=successful_operations
    )
    
    # 生成文件名
    safe_name = test_name.replace(' ', '_').replace('/', '_')
    filename = f"test_{safe_name}_generated.py"
    
    file_path = generator.save(filename, script)
    
    print(f"✅ 脚本已生成: {file_path}")
    print(f"📊 操作统计:")
    print(f"  总操作数: {len(client.operation_history)}")
    print(f"  成功操作: {len(successful_operations)}")
    print(f"  失败操作: {len(client.operation_history) - len(successful_operations)}")
    
    return file_path


if __name__ == "__main__":
    print("📝 从操作历史生成测试脚本")
    print("=" * 60)
    print()
    print("使用方法：")
    print("  1. 在代码中执行操作后，调用此函数生成脚本")
    print("  2. 或者直接导入使用：")
    print("     from mobile_mcp.tools.generate_script_from_history import generate_script_from_client")
    print("     generate_script_from_client(client, '测试名称', 'com.im30.way')")
    print()

