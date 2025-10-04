# 延迟加载优化 - 重命名避免与系统包冲突
import importlib
import time

# 简单的延迟加载缓存
_module_cache = {}
_load_times = {}

def lazy_import_cv2():
    """延迟导入OpenCV"""
    try:
        import cv2
        return cv2
    except ImportError:
        return None

def lazy_import_pil():
    """延迟导入PIL"""
    try:
        import PIL
        return PIL
    except ImportError:
        return None

def lazy_import_numpy():
    """延迟导入numpy"""
    try:
        import numpy
        return numpy
    except ImportError:
        return None

def lazy_import_paddleocr():
    """延迟导入PaddleOCR"""
    try:
        from paddleocr import PaddleOCR
        return PaddleOCR
    except ImportError:
        return None

def optimize_startup():
    """优化启动性能"""
    # 预加载关键模块（静默模式）
    critical_modules = ['tkinter', 'PIL', 'cv2', 'numpy']
    
    for module in critical_modules:
        start_time = time.time()
        try:
            importlib.import_module(module)
            load_time = time.time() - start_time
            # 静默加载，不显示调试信息
        except Exception as e:
            # 静默处理错误，不显示调试信息
            pass

def get_startup_stats():
    """获取启动统计信息"""
    total_time = sum(_load_times.values())
    return {
        'total_load_time': total_time,
        'modules_loaded': len(_module_cache),
        'load_times': _load_times.copy()
    }
