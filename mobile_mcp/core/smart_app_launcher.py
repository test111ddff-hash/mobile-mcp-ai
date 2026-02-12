#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能应用启动器
"""

class SmartAppLauncher:
    """智能应用启动器"""
    
    def __init__(self, mobile_client):
        self.mobile_client = mobile_client
    
    async def launch_app(self, package_name: str):
        """启动应用"""
        try:
            self.mobile_client.u2.app_start(package_name)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def launch_with_smart_wait(self, package_name: str, max_wait: int = 3, auto_close_ads: bool = True):
        """智能启动应用并等待"""
        try:
            import time
            # 启动应用
            self.mobile_client.u2.app_start(package_name)
            
            # 等待应用启动
            time.sleep(max_wait)
            
            # 检查是否启动成功
            current = self.mobile_client.u2.app_current()
            if current and current.get('package') == package_name:
                return {"success": True, "package": package_name}
            else:
                return {"success": True, "package": package_name, "warning": "应用可能未完全启动"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
