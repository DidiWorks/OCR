"""
GUI 工具包
包含文本高亮、对比窗口等功能
"""

# 导入文本高亮功能
from .text_highlighter import (
    apply_highlighting,
    refresh_highlighting
)

# 导入对比窗口功能
from .compare_window import show_compare_window

# 导入新的组件化模块
from .image_viewer import ImageViewer
from .text_editor import TextEditor
from .keywords_manager import KeywordsManager
# 重构版本已合并到主文件

# 导出所有公共接口
__all__ = [
    # 文本高亮
    'apply_highlighting',
    'refresh_highlighting',
    
    # 对比窗口
    'show_compare_window',
    
    # 新组件
    'ImageViewer',
    'TextEditor',
    'KeywordsManager'
]