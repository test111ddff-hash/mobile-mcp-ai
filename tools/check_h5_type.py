#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 H5 类型检测工具 - 判断是原生嵌入还是非原生嵌入

使用方法：
1. 打开你的 App，进入 H5 页面
2. 运行此脚本
3. 查看检测结果
"""
import uiautomator2 as u2
from xml.etree import ElementTree as ET


def check_h5_type():
    """检测 H5 页面类型"""
    print("=" * 70)
    print("🔍 H5 类型检测工具")
    print("=" * 70)
    print()
    
    # 连接设备
    d = u2.connect()
    print("✅ 已连接设备")
    print()
    
    # 获取 XML
    print("📱 正在获取页面结构...")
    xml_string = d.dump_hierarchy()
    
    # 解析 XML
    root = ET.fromstring(xml_string)
    
    # 查找 WebView
    webviews = root.findall(".//*[@class='android.webkit.WebView']")
    x5_webviews = root.findall(".//*[@class='com.tencent.smtt.webkit.WebView']")
    uc_webviews = root.findall(".//*[@class='com.uc.webview.export.WebView']")
    
    all_webviews = webviews + x5_webviews + uc_webviews
    
    if not all_webviews:
        print("❌ 未检测到 WebView，这不是 H5 页面")
        print("   当前页面是原生 Android 页面")
        return
    
    print(f"✅ 检测到 {len(all_webviews)} 个 WebView")
    print()
    
    # 分析每个 WebView
    for i, webview in enumerate(all_webviews, 1):
        print(f"{'=' * 70}")
        print(f"📦 WebView #{i}")
        print(f"{'=' * 70}")
        
        # WebView 类型
        webview_class = webview.get('class', '')
        print(f"类型: {webview_class}")
        
        if 'tencent.smtt' in webview_class:
            print("   → X5 内核（腾讯）- 通常支持原生化 ✅")
        elif 'uc.webview' in webview_class:
            print("   → UC 内核 - 通常支持原生化 ✅")
        elif 'android.webkit' in webview_class:
            print("   → 原生 WebView - 可能不支持原生化 ⚠️")
        
        print()
        
        # WebView 信息
        bounds = webview.get('bounds', '')
        resource_id = webview.get('resource-id', '')
        print(f"位置: {bounds}")
        if resource_id:
            print(f"ID: {resource_id}")
        print()
        
        # 统计子元素
        children = list(webview)
        print(f"子元素数量: {len(children)}")
        print()
        
        if len(children) == 0:
            print("🔴 结论: 非原生嵌入（Pure WebView）")
            print("   - WebView 内部是空的")
            print("   - UIAutomator2 看不到 H5 元素")
            print("   - 需要使用 Appium Context 切换或坐标点击")
            print()
            print("💡 解决方案:")
            print("   1. 使用 Appium Context 切换（推荐）")
            print("   2. 使用坐标点击")
            print("   3. 使用视觉识别")
        else:
            print("🟢 结论: 原生嵌入（Hybrid）")
            print("   - WebView 内部元素被原生化")
            print("   - UIAutomator2 可以看到 H5 元素")
            print("   - 可以直接使用智能定位")
            print()
            
            # 显示子元素类型统计
            element_types = {}
            for child in children:
                class_name = child.get('class', 'Unknown')
                element_types[class_name] = element_types.get(class_name, 0) + 1
            
            print("📊 元素类型分布:")
            for class_name, count in sorted(element_types.items(), key=lambda x: -x[1])[:10]:
                short_name = class_name.split('.')[-1]
                print(f"   - {short_name}: {count} 个")
            
            print()
            
            # 显示前5个有意义的元素
            meaningful_children = [
                c for c in children 
                if c.get('text') or c.get('content-desc') or c.get('resource-id')
            ][:5]
            
            if meaningful_children:
                print("📝 示例元素（前5个）:")
                for j, child in enumerate(meaningful_children, 1):
                    text = child.get('text', '')
                    desc = child.get('content-desc', '')
                    rid = child.get('resource-id', '')
                    class_name = child.get('class', '').split('.')[-1]
                    
                    parts = [f"{class_name}"]
                    if text:
                        parts.append(f"text='{text[:20]}'")
                    if desc:
                        parts.append(f"desc='{desc[:20]}'")
                    if rid:
                        parts.append(f"id='{rid[:30]}'")
                    
                    print(f"   {j}. {' | '.join(parts)}")
        
        print()
    
    print("=" * 70)
    print("✅ 检测完成！")
    print("=" * 70)


if __name__ == "__main__":
    try:
        check_h5_type()
    except KeyboardInterrupt:
        print("\n⚠️  已中断")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


