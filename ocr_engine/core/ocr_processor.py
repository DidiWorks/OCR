"""
OCR处理主逻辑
"""
import time
import gc
import os
import sys
from menu_utils import load_config
from ..engines.factory import get_engine
from ..formats.factory import get_format
from core import MemoryCleanupContext, file_manager

def get_config_path():
    """获取配置文件路径"""
    if getattr(sys, 'frozen', False):
        # 打包后的路径
        return os.path.join(sys._MEIPASS, 'config', 'settings.json')
    else:
        # 开发环境路径
        return 'config/settings.json'

def ocr_image(image_input, format_name=None):
    """主OCR处理函数"""
    start_time = time.time()
    
    with MemoryCleanupContext():
        try:
            # 加载配置
            config = load_config()
            
            # 读取当前引擎/格式名（兼容多种配置格式）
            engine_name = (config.get("engine", {}).get("current")
                          or config.get("current_ai_engine")
                          or "paddle")
            format_name = (config.get("format", {}).get("current")
                          or config.get("current_format")
                          or "steel_quality_v1")
            
            # 通过工厂获取引擎实例（惰性单例）
            engine = get_engine(engine_name)
            
            # 执行OCR识别
            text_lines = engine.recognize(image_input)
            
            # 检查OCR结果
            if not text_lines:
                return "OCR未识别到任何文本"
            
            # 通过工厂获取格式处理器并处理结果
            processor = get_format(format_name)
            result = processor.process(text_lines)
            return result
            
        except Exception as e:
            print("=" * 50)
            print("OCR处理失败")
            print("=" * 50)
            print(f"错误类型: {type(e).__name__}")
            print(f"错误信息: {e}")
            import traceback
            print(f"错误详情: {traceback.format_exc()}")
            print("=" * 50)
            return f"处理失败: {str(e)}"
        finally:
            # 强制垃圾回收
            gc.collect()
            # 检查磁盘空间，必要时清理
            file_manager.auto_cleanup_if_needed()
