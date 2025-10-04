# 图片查看器组件
# 从 compare_window.py 中提取的图片显示功能

import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
from ui import center_window, info, error

class ImageViewer:
    """图片查看器组件"""
    
    def __init__(self, parent, image):
        self.parent = parent
        self.original_image = image
        self.scale = 1.0
        self.drag = {"x": 0, "y": 0, "sx": 0, "sy": 0}
        
        # 获取图片尺寸
        if hasattr(image, 'save'):
            self.img_w, self.img_h = image.size
        else:
            self.img_w, self.img_h = image.size
    
    def create_canvas(self, parent_frame):
        """创建图片画布"""
        self.canvas = tk.Canvas(parent_frame, bg='white')
        
        # 创建滚动条
        self.hbar = tk.Scrollbar(parent_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.vbar = tk.Scrollbar(parent_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.config(xscrollcommand=self.hbar.set, yscrollcommand=self.vbar.set)
        
        # 设置滚动区域
        self.canvas.config(scrollregion=(0, 0, 2000, 2000))
        
        # 布局
        self.hbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.vbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 绑定事件
        self._bind_events()
        
        # 显示图片
        self._show_image()
        
        return self.canvas
    
    def _bind_events(self):
        """绑定事件"""
        self.canvas.bind("<MouseWheel>", self._on_wheel)
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<Button-3>", self._show_context_menu)
    
    def _show_image(self):
        """显示图片"""
        # 计算初始缩放比例
        self.scale = min(400/self.img_w, 400/self.img_h, 1.0)
        
        # 缩放图片
        new_size = (int(self.img_w * self.scale), int(self.img_h * self.scale))
        img_resized = self.original_image.resize(new_size, Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(img_resized)
        
        # 显示图片
        self.img_id = self.canvas.create_image(0, 0, anchor='nw', image=photo)
        self.canvas.config(scrollregion=(0, 0, new_size[0], new_size[1]))
        self.canvas.image = photo
    
    def _on_wheel(self, event):
        """滚轮事件 - 缩放"""
        if event.state & 0x0004:  # Ctrl
            self.scale = max(0.2, min(5.0, self.scale * (1.1 if event.delta > 0 else 1/1.1)))
            self._redraw()
            return "break"
        else:
            self.canvas.yview_scroll(-1 * int(event.delta/120), "units")
            return "break"
    
    def _on_press(self, event):
        """鼠标按下事件"""
        self.drag["x"], self.drag["y"] = event.x, event.y
        self.drag["sx"], self.drag["sy"] = self.canvas.xview()[0], self.canvas.yview()[0]
    
    def _on_drag(self, event):
        """鼠标拖拽事件"""
        dx, dy = event.x - self.drag["x"], event.y - self.drag["y"]
        x_move = -dx / max(1, self.canvas.winfo_width())
        y_move = -dy / max(1, self.canvas.winfo_height())
        self.canvas.xview_moveto(self.drag["sx"] + x_move)
        self.canvas.yview_moveto(self.drag["sy"] + y_move)
    
    def _redraw(self):
        """重绘图片"""
        new_size = (int(self.img_w * self.scale), int(self.img_h * self.scale))
        img_resized = self.original_image.resize(new_size, Image.Resampling.LANCZOS)
        new_photo = ImageTk.PhotoImage(img_resized)
        self.canvas.itemconfig(self.img_id, image=new_photo)
        self.canvas.config(scrollregion=(0, 0, new_size[0], new_size[1]))
        self.canvas.image = new_photo
    
    def _show_context_menu(self, event):
        """显示右键菜单"""
        context_menu = tk.Menu(self.parent, tearoff=0)
        context_menu.add_command(label="保存图片", command=self._save_image)
        context_menu.post(event.x_root, event.y_root)
    
    def _save_image(self):
        """保存图片"""
        try:
            file_path = filedialog.asksaveasfilename(
                title="保存图片",
                defaultextension=".png",
                filetypes=[
                    ("PNG图片", "*.png"),
                    ("JPEG图片", "*.jpg"),
                    ("所有文件", "*.*")
                ]
            )
            if file_path:
                self.original_image.save(file_path)
                info("保存成功", f"图片已保存到: {file_path}", parent=self.parent)
        except Exception as e:
            error("保存失败", f"保存图片时出错: {str(e)}", parent=self.parent)

