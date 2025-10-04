# 重构后的对比窗口
# 使用模块化组件，功能完全不变

import tkinter as tk
from PIL import Image
from ui import center_window
from .image_viewer import ImageViewer
from .text_editor import TextEditor
from .keywords_manager import KeywordsManager
from .text_highlighter import apply_highlighting, refresh_highlighting

def show_compare_window(parent, image_input, text):
    """显示对比窗口 - 重构版本"""
    win = tk.Toplevel(parent)
    win.lift()
    win.focus_force()
    win.title('图片与识别结果对比')
    win.geometry("1000x700")
    center_window(win, 1000, 700)
    
    # 创建窗口控制菜单栏
    _create_menu_bar(win)
    
    # 处理图片
    if hasattr(image_input, 'save'):
        original_img = image_input
    else:
        original_img = Image.open(image_input)
    
    # 创建工具栏
    toolbar = _create_toolbar(win)
    
    # 创建主面板
    paned = tk.PanedWindow(win, orient=tk.HORIZONTAL)
    paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    
    # 左侧：图片区域 - 使用新的 ImageViewer 组件
    image_frame = tk.Frame(paned, width=400, height=400)
    paned.add(image_frame, minsize=300)
    
    image_viewer = ImageViewer(win, original_img)
    image_viewer.create_canvas(image_frame)
    
    # 右侧：文本区域 - 使用新的 TextEditor 组件
    text_frame = tk.Frame(paned, width=500, height=400)
    paned.add(text_frame, minsize=400)
    
    text_editor = TextEditor(win)
    text_widget = text_editor.create_text_widget(text_frame)
    
    # 插入文本并应用高亮
    text_editor.insert_text(text)
    
    # 关键词管理区域 - 使用新的 KeywordsManager 组件
    keywords_frame = tk.Frame(win)
    keywords_frame.pack(fill=tk.X, padx=10, pady=6)
    
    keywords_manager = KeywordsManager(win)
    keywords_editor = keywords_manager.create_keywords_editor(keywords_frame)
    
    # 设置高亮更新回调
    def update_highlighting(keywords):
        """更新高亮"""
        refresh_highlighting(text_widget, keywords)
    
    keywords_manager.set_highlight_callback(update_highlighting)
    
    # 应用初始高亮
    current_keywords = keywords_manager.get_keywords()
    apply_highlighting(text_widget, current_keywords)
    
    # 筛选功能
    filter_mode = [False]
    original_text = [""]
    
    def toggle_filter():
        """切换筛选模式"""
        if not filter_mode[0]:
            # 进入筛选模式：只显示包含高亮关键词的行
            original_text[0] = text_widget.get("1.0", tk.END)
            filter_highlighted_lines()
            btn_filter.config(text="显示全部")
        else:
            # 退出筛选模式：显示所有行
            text_widget.delete("1.0", tk.END)
            text_widget.insert("1.0", original_text[0])
            current_keywords = keywords_manager.get_keywords()  # 获取最新关键词
            apply_highlighting(text_widget, current_keywords)
            btn_filter.config(text="筛选高亮")
        filter_mode[0] = not filter_mode[0]

    def filter_highlighted_lines():
        """筛选包含高亮关键词的行"""
        all_lines = text_widget.get("1.0", tk.END).split('\n')
        highlighted_lines = []
        current_keywords = keywords_manager.get_keywords()  # 获取最新关键词
        
        for line in all_lines:
            if line.strip() and has_highlighted_keywords(line):
                highlighted_lines.append(line)
        
        # 更新显示
        text_widget.delete("1.0", tk.END)
        text_widget.insert("1.0", '\n'.join(highlighted_lines))
        apply_highlighting(text_widget, current_keywords)

    def has_highlighted_keywords(line):
        """检查行是否包含任何关键词"""
        current_keywords = keywords_manager.get_keywords()  # 获取最新关键词
        for keyword in current_keywords:
            if keyword in line:
                return True
        return False
    
    def re_recognize_image():
        """再次识别图片"""
        try:
            # 禁用按钮，防止重复点击
            btn_re_recognize.config(state="disabled", text="识别中...")
            
            # 更新状态栏
            status_label.config(text="正在重新识别...")
            
            # 获取当前图片
            current_image = original_img
            
            # 异步执行OCR识别
            def ocr_worker():
                """OCR工作函数"""
                from ocr_engine import ocr_image
                return ocr_image(current_image)
            
            def on_ocr_complete(new_text):
                """OCR完成回调"""
                # 更新文本显示
                text_editor.clear_text()
                text_editor.insert_text(new_text)
                
                # 重新应用关键词高亮
                current_keywords = keywords_manager.get_keywords()
                apply_highlighting(text_widget, current_keywords)
                
                # 恢复按钮状态
                btn_re_recognize.config(state="normal", text="再次识别")
                
                # 更新状态栏
                status_label.config(text="识别完成")
                
                # 显示成功提示
                from ui import info
                info("识别完成", "图片已重新识别完成", parent=win)
            
            def on_ocr_error(error):
                """OCR错误回调"""
                # 恢复按钮状态
                btn_re_recognize.config(state="normal", text="再次识别")
                
                # 更新状态栏
                status_label.config(text="识别失败")
                
                # 显示错误提示
                from ui import error
                error("识别失败", f"重新识别时发生错误：{str(error)}", parent=win)
            
            # 使用异步处理器
            from core import async_with_progress
            async_with_progress(
                win,
                ocr_worker,
                on_complete=on_ocr_complete,
                on_error=on_ocr_error
            )
            
        except Exception as e:
            # 恢复按钮状态
            btn_re_recognize.config(state="normal", text="再次识别")
            
            # 显示错误提示
            from ui import error
            error("识别失败", f"重新识别时发生错误：{str(e)}", parent=win)
    
    # 再次识别按钮
    btn_re_recognize = tk.Button(
        toolbar, 
        text="再次识别", 
        command=lambda: re_recognize_image(),
        width=8,
        font=("Arial", 9),
        relief=tk.RAISED,
        bd=1,
        bg="#f0f0f0",
        fg="black"
    )
    btn_re_recognize.pack(side=tk.RIGHT, padx=5, pady=5)
    
    # 筛选按钮
    btn_filter = tk.Button(
        toolbar, 
        text="筛选高亮", 
        command=toggle_filter,
        width=8,
        font=("Arial", 9),
        relief=tk.RAISED,
        bd=1,
        bg="#f0f0f0",
        fg="black"
    )
    btn_filter.pack(side=tk.RIGHT, padx=5, pady=5)
    
    # 状态栏
    status = tk.Frame(win, height=25)
    status.pack(fill=tk.X, padx=5, pady=2)
    status_label = tk.Label(status, text="说明: Ctrl+滚轮调字体", anchor='w', font=("Arial", 8))
    status_label.pack(side=tk.LEFT)
    
    win.wait_window()

def _create_menu_bar(win):
    """创建菜单栏"""
    control_menubar = tk.Menu(win,
                              bg='#f8f8f8',  
                              fg='#333333',
                              activebackground='#e0e0e0',
                              activeforeground='#000000', 
                              font=("Microsoft YaHei", 9),
                              relief=tk.FLAT,
                              bd=0) 
    
    window_menu = tk.Menu(control_menubar,
                        tearoff=0,
                        bg='#f8f8f8',
                        fg='#333333',
                        activebackground='#e0e0e0',
                        activeforeground='#000000',
                        font=("Microsoft YaHei", 9),
                        relief=tk.FLAT,
                        bd=0)
    control_menubar.add_cascade(label=' ', menu=window_menu)
    
    # 最大化/还原按钮
    is_maximized = [False]
    def toggle_maximize():
        if is_maximized[0]:
            win.state('normal')
            window_menu.entryconfig(0, label="最大化")
            is_maximized[0] = False
        else:
            win.state('zoomed')
            window_menu.entryconfig(0, label="还原")
            is_maximized[0] = True

    window_menu.add_command(label="最大化", command=toggle_maximize)
    window_menu.add_command(label="最小化", command=lambda: win.iconify())
    window_menu.add_separator()
    window_menu.add_command(label="关闭", command=win.destroy)
    
    win.config(menu=control_menubar)

def _create_toolbar(win):
    """创建工具栏"""
    toolbar = tk.Frame(win, bg='#f8f8f8', height=40)
    toolbar.pack(fill=tk.X, padx=5, pady=2)
    toolbar.pack_propagate(False)
    
    # 工具栏标题
    tk.Label(toolbar, text="图片与识别结果对比", font=("Microsoft YaHei", 10, "bold"), 
             bg='#f8f8f8', fg='#333333').pack(side=tk.LEFT, padx=10, pady=8)
    
    return toolbar
