# 异步处理优化
import threading
import time
import queue
from typing import Callable, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import tkinter as tk

class AsyncProcessor:
    """异步处理器 - 提供高效的异步任务处理"""
    
    def __init__(self, max_workers=3):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.task_queue = queue.Queue()
        self.results = {}
        self.task_id_counter = 0
        
    def submit_task(self, func: Callable, *args, **kwargs) -> int:
        """提交异步任务"""
        task_id = self.task_id_counter
        self.task_id_counter += 1
        
        future = self.executor.submit(func, *args, **kwargs)
        self.results[task_id] = future
        
        return task_id
    
    def get_result(self, task_id: int, timeout: Optional[float] = None) -> Any:
        """获取任务结果"""
        if task_id not in self.results:
            raise ValueError(f"任务ID {task_id} 不存在")
        
        future = self.results[task_id]
        try:
            return future.result(timeout=timeout)
        finally:
            # 清理已完成的任务
            if future.done():
                del self.results[task_id]
    
    def is_done(self, task_id: int) -> bool:
        """检查任务是否完成"""
        if task_id not in self.results:
            return True
        return self.results[task_id].done()
    
    def cancel_task(self, task_id: int) -> bool:
        """取消任务"""
        if task_id not in self.results:
            return False
        
        future = self.results[task_id]
        cancelled = future.cancel()
        if cancelled:
            del self.results[task_id]
        return cancelled
    
    def cleanup(self):
        """清理资源"""
        self.executor.shutdown(wait=False)
        self.results.clear()

# 全局异步处理器
async_processor = AsyncProcessor(max_workers=3)


def async_with_progress(parent, func: Callable, *args, 
                       title: str = "处理中...", 
                       message: str = "正在处理，请稍候...",
                       on_complete: Optional[Callable] = None,
                       on_error: Optional[Callable] = None) -> int:
    """简单异步执行 - 只更新状态栏"""
    
    def worker():
        try:
            result = func(*args)
            
            # 执行完成回调
            if on_complete:
                parent.after(0, lambda: on_complete(result))
                
            return result
            
        except Exception as e:
            # 执行错误回调
            if on_error:
                parent.after(0, lambda: on_error(e))
            else:
                # 默认错误处理
                parent.after(0, lambda: show_error(parent, "处理失败", str(e)))
            
            raise e
    
    # 提交异步任务
    task_id = async_processor.submit_task(worker)
    
    # 返回任务ID，可用于取消
    return task_id

def show_error(parent, title: str, message: str):
    """显示错误对话框"""
    import tkinter.messagebox as mb
    mb.showerror(title, message, parent=parent)

def show_info(parent, title: str, message: str):
    """显示信息对话框"""
    import tkinter.messagebox as mb
    mb.showinfo(title, message, parent=parent)

def cleanup_async_processor():
    """清理异步处理器"""
    async_processor.cleanup()
