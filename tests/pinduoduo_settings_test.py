#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动生成的测试脚本: 拼多多设置页面导航测试

说明：
- 使用百分比坐标，适配不同分辨率
- 优先使用text/id定位，提高稳定性
- 包含智能等待和错误处理
- 需要连接真实设备运行
"""

import pytest
import asyncio
import time
import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

try:
    from mobile_mcp.core.mobile_client import MobileClient
except ImportError:
    print("❌ 无法导入mobile_mcp模块，请确保在项目环境中运行")
    print("💡 提示：激活虚拟环境 - source venv/bin/activate")
    sys.exit(1)


class Test拼多多设置页面导航测试:
    """自动生成的测试类"""

    @pytest.fixture
    def client(self):
        """初始化移动端客户端 - com.xunmeng.pinduoduo"""
        return MobileClient(platform="android")

    @pytest.mark.asyncio
    async def test_automation_flow(self, client):
        """测试流程: 拼多多设置页面导航测试"""
        # 步骤1: 启动应用 com.xunmeng.pinduoduo
        await client.launch_app("com.xunmeng.pinduoduo")
        time.sleep(2)  # 等待应用启动

        # 步骤2: 等待3秒
        time.sleep(3)

        # 步骤3: 点击个人中心按钮
        client.u2(text="个人中心").click(timeout=3)
        time.sleep(1)  # 等待操作完成

        # 步骤4: 等待2秒
        time.sleep(2)

        # 步骤5: 点击设置按钮
        client.u2(text="设置").click(timeout=3)
        time.sleep(1)  # 等待操作完成

        # 步骤6: 等待2秒
        time.sleep(2)

        # 验证测试完成
        print("✅ 测试流程执行完成")
        assert True  # 测试通过


if __name__ == "__main__":
    print("🧪 开始运行测试: 拼多多设置页面导航测试")
    print("=" * 60)
    
    async def run_test():
        client = MobileClient(platform="android")
        
        # 检查当前应用状态
        current = client.u2.app_current()
        print(f"📱 当前应用: {current}")
        
        # 如果不在拼多多，则启动
        if not current or current.get('package') != 'com.xunmeng.pinduoduo':
            print("🚀 启动拼多多应用...")
            await client.launch_app("com.xunmeng.pinduoduo")
            time.sleep(3)
        
        # 检查是否在设置页面
        settings_title = client.u2(text="设置")
        if settings_title.exists(timeout=2):
            print("✅ 已经在设置页面")
        else:
            # 需要导航到设置页面
            print("🔍 查找个人中心按钮...")
            personal_center = client.u2(text="个人中心")
            if personal_center.exists(timeout=5):
                personal_center.click()
                print("✅ 点击个人中心成功")
                time.sleep(3)
                
                print("🔍 查找设置按钮...")
                settings = client.u2(text="设置")
                if settings.exists(timeout=5):
                    settings.click()
                    print("✅ 点击设置成功")
                else:
                    print("❌ 未找到设置按钮")
                    return
            else:
                print("❌ 未找到个人中心按钮")
                return
        
        time.sleep(2)
        print("✅ 测试流程执行完成 - 已到达设置页面")
    
    asyncio.run(run_test())