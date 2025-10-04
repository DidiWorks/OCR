import tkinter as tk
from ui import center_window
from menu_utils import create_menu_bar
from .flows import capture_and_recognize, select_and_recognize
from .logger import logger, on_exit
from core import cleanup_on_exit, auto_cleanup_on_startup, optimize_startup, cleanup_async_processor


def run_app():
    root = tk.Tk()
    root.title("OCR自动识别工具 v1.0")
    root.geometry("300x200")
    center_window(root, 300, 200)

    # 启动日志
    logger.log_ocr_start("程序启动")
    
    # 优化启动性能
    optimize_startup()
    
    # 启动时自动清理文件
    auto_cleanup_on_startup()

    # 菜单
    create_menu_bar(root, lambda: select_and_recognize(root))

    # 主界面
    frame = tk.Frame(root, padx=20, pady=20)
    frame.pack(expand=True, fill=tk.BOTH)

    # 按钮
    btn_capture = tk.Button(frame, text="拍照识别", command=lambda: capture_and_recognize(root))
    btn_capture.pack(pady=10, fill=tk.X)

    btn_select = tk.Button(frame, text="选择图片识别", command=lambda: select_and_recognize(root))
    btn_select.pack(pady=10, fill=tk.X)

    # 状态栏
    status_frame = tk.Frame(root)
    status_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=2)
    status_label = tk.Label(status_frame, text="就绪", relief=tk.SUNKEN, anchor="w")
    status_label.pack(fill=tk.X)

    # 将按钮和状态栏传递给flows
    root.btn_capture = btn_capture
    root.btn_select = btn_select
    root.status_label = status_label

    # 注册退出清理
    def cleanup_and_exit():
        try:
            cleanup_on_exit()
            cleanup_async_processor()
            on_exit(root)
            root.quit()  # 强制退出主循环
            root.destroy()  # 销毁窗口
        except Exception as e:
            # 忽略退出时的错误
            pass
    
    root.protocol("WM_DELETE_WINDOW", cleanup_and_exit)
    root.mainloop()