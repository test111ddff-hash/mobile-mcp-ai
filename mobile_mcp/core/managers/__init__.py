#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
管理器模块初始化
"""

from .screenshot_manager import ScreenshotManager
from .click_manager import ClickManager
from .element_manager import ElementManager

__all__ = ['ScreenshotManager', 'ClickManager', 'ElementManager']
