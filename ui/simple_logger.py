# 精简日志系统
import logging
import os
import gc
from datetime import datetime
from core import memory_manager, file_manager

class SimpleLogger:
    """精简日志系统 - 只保留核心功能"""
    
    def __init__(self, log_dir="logs", log_level="INFO"):
        self.log_dir = log_dir
        self.setup_logging(log_level)
        
    def setup_logging(self, log_level):
        """设置基础日志配置"""
        # 创建日志目录
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        
        # 启动时清理旧日志文件
        file_manager.cleanup_temp_directory(self.log_dir)
            
        # 移除所有已存在的handler
        for h in logging.root.handlers[:]:
            logging.root.removeHandler(h)
            
        # 设置简单日志格式
        log_format = '%(asctime)s - %(levelname)s - %(message)s'
        date_format = '%Y-%m-%d %H:%M:%S'
        
        # 配置日志 - 只输出到文件
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format=log_format,
            datefmt=date_format,
            handlers=[
                # 文件输出 - 按日期分割
                logging.FileHandler(
                    os.path.join(self.log_dir, f"ocr_{datetime.now().strftime('%Y%m%d')}.log"),
                    encoding='utf-8'
                )
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        
    def log_ocr_start(self, message):
        """记录OCR开始"""
        self.logger.info(f"OCR开始: {message}")
        
    def log_ocr_result(self, operation, result, confidence=None, processing_time=None):
        """记录OCR结果"""
        msg = f"{operation}: {result}"
        if confidence:
            msg += f" (置信度: {confidence:.2f})"
        if processing_time:
            msg += f" (耗时: {processing_time:.2f}s)"
        self.logger.info(msg)
        
    def log_ocr_error(self, operation, error_msg):
        """记录OCR错误"""
        self.logger.error(f"{operation}错误: {error_msg}")
        
    def log_file_generation(self, operation, file_path, content_summary=None):
        """记录文件生成"""
        msg = f"{operation}: {file_path}"
        if content_summary:
            msg += f" - {content_summary}"
        self.logger.info(msg)

# 创建全局日志实例
logger = SimpleLogger()

def on_exit(root):
    """程序退出时的清理"""
    import shutil
    import os
    
    # 清理所有临时文件
    try:
        cleanup_results = file_manager.cleanup_all_temp_dirs()
        total_cleaned = 0
        total_size_saved = 0
        
        for dir_name, result in cleanup_results.items():
            cleaned = result['old_files_cleaned'] + result['excess_files_cleaned']
            size_saved = result['total_size_before'] - result['total_size_after']
            total_cleaned += cleaned
            total_size_saved += size_saved
            
            if cleaned > 0:
                logger.log_file_generation("清理", f"{dir_name}目录", f"清理{cleaned}个文件，节省{file_manager.format_size(size_saved)}")
        
        # 完全删除 captured 文件夹（按原设计）
        if os.path.exists('captured'):
            try:
                shutil.rmtree('captured')
                logger.log_file_generation("清理", "captured目录", "完全删除captured文件夹")
            except Exception as e:
                logger.log_file_generation("清理", "captured目录", f"删除失败: {e}")
                
    finally:
        # 执行内存清理
        memory_manager.cleanup_memory(force=True)
        memory_manager.cleanup_large_objects()
        
        logger.log_file_generation("程序", "退出", "清理资源并退出")
        root.destroy()
