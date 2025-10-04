# 简单文件管理优化
import os
import shutil
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional

class SimpleFileManager:
    """简单文件管理器 - 提供基础的文件清理和空间管理功能"""
    
    def __init__(self):
        self.temp_dirs = ['captured', 'output', 'logs']
        self.max_file_age_days = 7  # 文件最大保存天数
        self.max_temp_files = 50    # 临时文件最大数量
        self.max_log_files = 10     # 日志文件最大数量
        
    def get_directory_size(self, path: str) -> int:
        """获取目录大小（字节）"""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.exists(filepath):
                        total_size += os.path.getsize(filepath)
        except Exception:
            pass
        return total_size
    
    def format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes < 1024:
            return f"{size_bytes}B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f}KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f}MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f}GB"
    
    def cleanup_old_files(self, directory: str, max_age_days: int = None) -> int:
        """清理指定目录中的旧文件"""
        if max_age_days is None:
            max_age_days = self.max_file_age_days
            
        cleaned_count = 0
        cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)
        
        try:
            if not os.path.exists(directory):
                return 0
                
            for filename in os.listdir(directory):
                filepath = os.path.join(directory, filename)
                if os.path.isfile(filepath):
                    file_time = os.path.getmtime(filepath)
                    if file_time < cutoff_time:
                        try:
                            os.remove(filepath)
                            cleaned_count += 1
                        except Exception as e:
                            pass  # 静默处理错误
        except Exception as e:
            pass  # 静默处理错误
            
        return cleaned_count
    
    def cleanup_excess_files(self, directory: str, max_files: int, keep_newest: bool = True) -> int:
        """清理超出数量限制的文件"""
        cleaned_count = 0
        
        try:
            if not os.path.exists(directory):
                return 0
                
            files = []
            for filename in os.listdir(directory):
                filepath = os.path.join(directory, filename)
                if os.path.isfile(filepath):
                    file_time = os.path.getmtime(filepath)
                    files.append((filepath, file_time))
            
            # 按时间排序
            files.sort(key=lambda x: x[1], reverse=keep_newest)
            
            # 删除超出限制的文件
            if len(files) > max_files:
                for filepath, _ in files[max_files:]:
                    try:
                        os.remove(filepath)
                        cleaned_count += 1
                    except Exception as e:
                        pass  # 静默处理错误
                        
        except Exception as e:
            pass  # 静默处理错误
            
        return cleaned_count
    
    def cleanup_temp_directory(self, directory: str) -> Dict[str, int]:
        """清理临时目录"""
        result = {
            'old_files_cleaned': 0,
            'excess_files_cleaned': 0,
            'total_size_before': 0,
            'total_size_after': 0
        }
        
        try:
            if not os.path.exists(directory):
                return result
                
            # 记录清理前大小
            result['total_size_before'] = self.get_directory_size(directory)
            
            # 清理旧文件
            result['old_files_cleaned'] = self.cleanup_old_files(directory)
            
            # 清理超出数量的文件
            if directory == 'captured':
                result['excess_files_cleaned'] = self.cleanup_excess_files(directory, self.max_temp_files)
            elif directory == 'logs':
                result['excess_files_cleaned'] = self.cleanup_excess_files(directory, self.max_log_files)
            
            # 记录清理后大小
            result['total_size_after'] = self.get_directory_size(directory)
            
        except Exception as e:
            pass  # 静默处理错误
            
        return result
    
    def cleanup_all_temp_dirs(self) -> Dict[str, Dict[str, int]]:
        """清理所有临时目录"""
        results = {}
        
        for temp_dir in self.temp_dirs:
            if os.path.exists(temp_dir):
                results[temp_dir] = self.cleanup_temp_directory(temp_dir)
            else:
                results[temp_dir] = {
                    'old_files_cleaned': 0,
                    'excess_files_cleaned': 0,
                    'total_size_before': 0,
                    'total_size_after': 0
                }
        
        return results
    
    def get_disk_usage_info(self) -> Dict[str, any]:
        """获取磁盘使用信息"""
        try:
            import shutil
            total, used, free = shutil.disk_usage('.')
            
            return {
                'total': total,
                'used': used,
                'free': free,
                'total_formatted': self.format_size(total),
                'used_formatted': self.format_size(used),
                'free_formatted': self.format_size(free),
                'usage_percent': (used / total) * 100
            }
        except Exception as e:
            pass  # 静默处理错误
            return {
                'total': 0, 'used': 0, 'free': 0,
                'total_formatted': '0B', 'used_formatted': '0B', 'free_formatted': '0B',
                'usage_percent': 0
            }
    
    def should_cleanup_disk(self, threshold_percent: float = 85.0) -> bool:
        """判断是否需要清理磁盘空间"""
        disk_info = self.get_disk_usage_info()
        return disk_info['usage_percent'] > threshold_percent
    
    def auto_cleanup_if_needed(self, threshold_percent: float = 85.0) -> bool:
        """如果需要则自动清理"""
        if self.should_cleanup_disk(threshold_percent):
            pass  # 静默处理
            results = self.cleanup_all_temp_dirs()
            
            total_cleaned = 0
            total_size_saved = 0
            
            for dir_name, result in results.items():
                total_cleaned += result['old_files_cleaned'] + result['excess_files_cleaned']
                total_size_saved += result['total_size_before'] - result['total_size_after']
            
            pass  # 静默处理
            return True
        
        return False

# 全局文件管理器实例
file_manager = SimpleFileManager()

def cleanup_temp_files():
    """清理临时文件"""
    results = file_manager.cleanup_all_temp_dirs()
    
    total_cleaned = 0
    total_size_saved = 0
    
    for dir_name, result in results.items():
        cleaned = result['old_files_cleaned'] + result['excess_files_cleaned']
        size_saved = result['total_size_before'] - result['total_size_after']
        
        if cleaned > 0 or size_saved > 0:
            pass  # 静默处理
            total_cleaned += cleaned
            total_size_saved += size_saved
    
    if total_cleaned > 0:
        pass  # 静默处理
    else:
        pass  # 静默处理

def get_disk_info() -> str:
    """获取磁盘信息字符串"""
    disk_info = file_manager.get_disk_usage_info()
    return f"磁盘使用: {disk_info['used_formatted']}/{disk_info['total_formatted']} ({disk_info['usage_percent']:.1f}%)"

def auto_cleanup_on_startup():
    """启动时自动清理"""
    # 启动时检查磁盘空间（静默模式）
    file_manager.auto_cleanup_if_needed()
