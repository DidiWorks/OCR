# 核心功能模块
# 统一导入入口，方便使用

# 内存管理
from .memory_manager import memory_manager, cleanup_on_exit, auto_cleanup, MemoryCleanupContext

# 文件管理
from .file_manager import file_manager, cleanup_temp_files, get_disk_info, auto_cleanup_on_startup

# 异步处理
from .async_processor import async_processor, async_with_progress, cleanup_async_processor, show_error, show_info

# 模块加载
from .module_loader import optimize_startup, get_startup_stats, lazy_import_cv2, lazy_import_pil, lazy_import_numpy, lazy_import_paddleocr

__all__ = [
    # 内存管理
    'memory_manager', 'cleanup_on_exit', 'auto_cleanup', 'MemoryCleanupContext',
    # 文件管理
    'file_manager', 'cleanup_temp_files', 'get_disk_info', 'auto_cleanup_on_startup',
    # 异步处理
    'async_processor', 'async_with_progress', 'cleanup_async_processor', 'show_error', 'show_info',
    # 模块加载
    'optimize_startup', 'get_startup_stats', 'lazy_import_cv2', 'lazy_import_pil', 'lazy_import_numpy', 'lazy_import_paddleocr'
]
