import time
import tkinter as tk
from tkinter import filedialog, ttk

from ui import CameraWindow
from cropper import select_and_crop_enhanced
from ocr_engine import ocr_image

from menu_utils import load_config
from .logger import logger
from core import memory_manager, MemoryCleanupContext, auto_cleanup, async_with_progress, show_error, show_info


@auto_cleanup
def capture_and_recognize(root):
    """拍照识别流程"""
    logger.log_ocr_start("开始拍照识别流程")
    
    # 设置状态
    root.status_label.config(text="正在打开摄像头...")
    root.btn_capture.config(state="disabled", text="拍照识别中...")
    root.config(cursor="wait")
    
    with MemoryCleanupContext():
        try:
            camera_win = CameraWindow(root, save_dir='captured')
            root.wait_window(camera_win)
            img_path = camera_win.image_path

            if img_path:
                logger.log_ocr_result("拍照", f"拍照成功: {img_path}", 1.0, 0.0)
                root.status_label.config(text="正在处理图片...")

                cropped_img = select_and_crop_enhanced(img_path)
                if cropped_img:
                    # OCR识别改为异步
                    _async_ocr_and_compare(root, cropped_img)
                else:
                    logger.log_ocr_error("截图选择", "用户取消截图")
                    root.status_label.config(text="用户取消截图")
            else:
                logger.log_ocr_error("拍照", "拍照失败或用户取消")
                root.status_label.config(text="拍照失败或用户取消")
        except Exception as e:
            logger.log_ocr_error("拍照识别", f"发生错误: {str(e)}")
            root.status_label.config(text=f"发生错误: {str(e)}")
        finally:
            # 恢复状态
            root.btn_capture.config(state="normal", text="拍照识别")
            root.config(cursor="")
            root.status_label.config(text="就绪")

def _async_ocr_and_compare(root, cropped_img):
    """异步OCR识别和对比"""
    
    def ocr_worker():
        """OCR工作函数"""
        return ocr_image(cropped_img)
    
    def on_ocr_complete(result):
        """OCR完成回调"""
        _show_result(root, cropped_img, result)
    
    def on_ocr_error(error):
        """OCR错误回调"""
        root.status_label.config(text=f"OCR识别失败: {str(error)}")
        logger.log_ocr_error("OCR识别", str(error))
    
    # 使用异步处理器
    async_with_progress(
        root,
        ocr_worker,
        on_complete=on_ocr_complete,
        on_error=on_ocr_error
    )

def _show_result(root, cropped_img, result):
    """显示识别结果"""
    from gui_utils.compare_window import show_compare_window
    show_compare_window(root, cropped_img, result)
    root.status_label.config(text="识别完成")


@auto_cleanup
def select_and_recognize(root):
    """选择图片识别流程"""
    logger.log_ocr_start("开始选择图片识别流程")
    
    # 设置状态
    root.status_label.config(text="正在选择图片...")
    root.btn_select.config(state="disabled", text="选择图片中...")
    root.config(cursor="wait")
    
    with MemoryCleanupContext():
        try:
            img_path = filedialog.askopenfilename(filetypes=[('Image Files', '*.jpg;*.png;*.bmp')], parent=root)
            if img_path:
                logger.log_ocr_result("选择图片", f"选择图片: {img_path}", 1.0, 0.0)
                root.status_label.config(text="正在处理图片...")

                cropped_img = select_and_crop_enhanced(img_path)
                if cropped_img:
                    _ocr_then_export_and_compare(root, cropped_img)
                else:
                    logger.log_ocr_error("截图选择", "用户取消截图")
                    root.status_label.config(text="用户取消截图")
            else:
                logger.log_ocr_error("选择图片", "用户取消选择图片")
                root.status_label.config(text="用户取消选择图片")
        except Exception as e:
            logger.log_ocr_error("选择图片识别", f"发生错误: {str(e)}")
            root.status_label.config(text=f"发生错误: {str(e)}")
        finally:
            # 恢复状态
            root.btn_select.config(state="normal", text="选择图片识别")
            root.config(cursor="")
            root.status_label.config(text="就绪")


def _ocr_then_export_and_compare(root, cropped_img):
    """OCR -> 导出 -> 对比窗口"""
    
    def ocr_worker():
        """OCR工作函数"""
        start_time = time.time()
        text = ocr_image(cropped_img)
        processing_time = time.time() - start_time
        logger.log_ocr_result("OCR识别", text, 0.9, processing_time)
        return text
    
    def on_ocr_complete(text):
        """OCR完成回调"""
        root.status_label.config(text="识别完成，正在显示结果...")
        
        # 对比窗口
        from gui_utils import show_compare_window
        show_compare_window(root, cropped_img, text)
        
        # 恢复状态
        root.status_label.config(text="就绪")
    
    def on_ocr_error(error):
        """OCR错误回调"""
        root.status_label.config(text=f"OCR识别失败: {str(error)}")
        logger.log_ocr_error("OCR识别", str(error))
    
    # 使用异步处理器
    async_with_progress(
        root,
        ocr_worker,
        on_complete=on_ocr_complete,
        on_error=on_ocr_error
    )


