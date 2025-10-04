#原来摄像头结构
import tkinter as tk
from .window_utils import error
import os
from datetime import datetime
from .window_utils import center_window
from core import file_manager, lazy_import_cv2, lazy_import_pil

class CameraWindow(tk.Toplevel):
    """
    一个Tkinter顶级窗口, 用于显示摄像头预览、拍照和返回路径。
    """
    def __init__(self, master, **kwargs):
        self.save_dir = kwargs.pop('save_dir')
        super().__init__(master, **kwargs)

        self.title("摄像头 (按空格拍照, ESC或点X退出)")
        self.geometry("800x650")
        center_window(self, 800, 650)
        self.image_path = None

        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
        
        # 拍照前清理旧文件
        file_manager.cleanup_temp_directory(self.save_dir)

        # 延迟加载OpenCV
        cv2 = lazy_import_cv2()
        if cv2 is None:
            error("摄像头错误", "OpenCV未安装!", parent=self)
            self.destroy()
            return

        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            error("摄像头错误", "无法打开摄像头!", parent=self)
            self.destroy()
            return 

        self.canvas = tk.Label(self)
        self.canvas.pack(pady=10, padx=10)

        self.bind('<space>', self.capture_image_event)
        self.bind('<Escape>', self.close_window_event)
        self.protocol("WM_DELETE_WINDOW", self.close_window)

        self.update_frame()

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            self.current_frame_cv = frame
            
            # 延迟加载OpenCV和PIL
            cv2 = lazy_import_cv2()
            pil_module = lazy_import_pil()
            
            if cv2 is None or pil_module is None:
                self.close_window()
                return
            
            img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img_pil = pil_module.Image.fromarray(img)
            img_tk = pil_module.ImageTk.PhotoImage(image=img_pil)

            self.canvas.imgtk = img_tk
            self.canvas.config(image=img_tk)
      
            self.after(15, self.update_frame)
        else:
            self.close_window()

    def capture_image_event(self, event=None):
        """由空格键触发的拍照事件"""
        filename = datetime.now().strftime('%Y%m%d_%H%M%S') + '.jpg'     
        self.image_path = os.path.join(self.save_dir, filename)

        # 延迟加载OpenCV
        cv2 = lazy_import_cv2()
        if cv2 is not None:
            cv2.imwrite(self.image_path, self.current_frame_cv)
       
        self.close_window()

    def close_window_event(self, event=None):
        """由ESC键触发的关闭事件"""
        self.close_window()

    def close_window(self):
        """统一的窗口关闭逻辑"""
        if self.cap.isOpened():
            self.cap.release()
        self.destroy()