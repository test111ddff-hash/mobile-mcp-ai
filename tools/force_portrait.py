#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""强制旋转回竖屏"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend"))

from mobile_mcp.core.mobile_client import MobileClient

client = MobileClient()
client.force_portrait()
print("✅ 已强制旋转回竖屏")

