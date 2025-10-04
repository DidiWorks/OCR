# 简单内存管理优化
import gc

class SimpleMemoryManager:
    """简单内存管理器 - 只提供基础的内存清理功能"""
    
    def __init__(self):
        self._cleanup_callbacks = []
        
    def add_cleanup_callback(self, callback):
        """添加清理回调函数"""
        self._cleanup_callbacks.append(callback)
    
    def cleanup_memory(self, force=False):
        """执行内存清理"""
        # 执行垃圾回收
        collected = gc.collect()
        
        # 执行自定义清理回调
        for callback in self._cleanup_callbacks:
            try:
                callback()
            except Exception as e:
                pass  # 静默处理错误
        
        if force:
            # 静默清理，不显示调试信息
            pass
        
    def cleanup_large_objects(self):
        """清理大型对象"""
        # 清理可能的大对象
        try:
            # 清理PIL图像缓存
            from PIL import Image
            Image._show.__dict__.clear()
        except:
            pass
            
        # 清理tkinter相关缓存
        try:
            import tkinter as tk
            # 清理tkinter的字体缓存
            if hasattr(tk, '_font_cache'):
                tk._font_cache.clear()
        except:
            pass

# 全局内存管理器实例
memory_manager = SimpleMemoryManager()

def cleanup_on_exit():
    """程序退出时的内存清理"""
    memory_manager.cleanup_memory(force=True)
    memory_manager.cleanup_large_objects()

# 装饰器：自动内存清理
def auto_cleanup(func):
    """装饰器：函数执行后自动清理内存"""
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            memory_manager.cleanup_memory()
    return wrapper

# 上下文管理器：内存清理
class MemoryCleanupContext:
    """内存清理上下文管理器"""
    
    def __init__(self, cleanup_on_exit=True):
        self.cleanup_on_exit = cleanup_on_exit
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.cleanup_on_exit:
            memory_manager.cleanup_memory()
