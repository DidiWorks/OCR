"""
菜单栏创建模块
负责创建主菜单栏和菜单项
"""
import tkinter as tk
from .dialogs import  show_about, show_recognition_settings
from core import cleanup_temp_files, get_disk_info

def create_menu_bar(root, select_and_recognize_func):
    """创建圆润简约菜单栏"""
    menubar = tk.Menu(root, 
                     bg='#f8f8f8',           # 浅灰背景
                     fg='#333333',           # 深灰文字
                     activebackground='#e0e0e0',  # 悬停时浅灰
                     activeforeground='#000000',  # 悬停时黑色
                     font=("Microsoft YaHei", 9),  # 微软雅黑字体
                     relief=tk.FLAT,         # 扁平风格
                     bd=0)                   # 无边框
    root.config(menu=menubar)
    
    # 工具菜单 - 圆润简约风格
    tools_menu = tk.Menu(menubar, 
                        tearoff=0,
                        bg='#f8f8f8',
                        fg='#333333',
                        activebackground='#e0e0e0',
                        activeforeground='#000000',
                        font=("Microsoft YaHei", 9),
                        relief=tk.FLAT,
                        bd=0)
    menubar.add_cascade(label="工具", menu=tools_menu)
    tools_menu.add_command(label="识别设置", command=lambda: show_recognition_settings(root))

    # 帮助菜单 - 圆润简约风格
    help_menu = tk.Menu(menubar, 
                       tearoff=0,
                       bg='#f8f8f8',
                       fg='#333333',
                       activebackground='#e0e0e0',
                       activeforeground='#000000',
                       font=("Microsoft YaHei", 9),
                       relief=tk.FLAT,
                       bd=0)
    menubar.add_cascade(label=" 帮助", menu=help_menu)
    help_menu.add_command(label="关于", command=lambda: show_about(root))
    
    return menubar
