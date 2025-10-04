# 文本编辑器组件
# 从 compare_window.py 中提取的文本编辑功能

import tkinter as tk
from tkinter import font
from ui import error

class TextEditor:
    """文本编辑器组件"""
    
    def __init__(self, parent):
        self.parent = parent
        self.text_font_size = 12
        self.text_font = font.Font(family="Courier New", size=self.text_font_size)
        self.selected_column_index = None
        
    def create_text_widget(self, parent_frame):
        """创建文本控件"""
        self.text_box = tk.Text(
            parent_frame, width=60, height=24, font=self.text_font, wrap=tk.NONE,
            borderwidth=1, relief=tk.SUNKEN, state=tk.NORMAL, undo=True,
            tabs=('100p', '200p', '350p', '500p')
        )
        
        # 创建滚动条
        self.sbx = tk.Scrollbar(parent_frame, orient=tk.HORIZONTAL, command=self.text_box.xview)
        self.sby = tk.Scrollbar(parent_frame, orient=tk.VERTICAL, command=self.text_box.yview)
        
        # 设置滚动条命令
        self.text_box['xscrollcommand'] = self.sbx.set
        self.text_box['yscrollcommand'] = self.sby.set
        
        # 布局
        self.sbx.pack(side=tk.BOTTOM, fill=tk.X)
        self.sby.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 绑定事件
        self._bind_events()
        
        return self.text_box
    
    def _bind_events(self):
        """绑定事件"""
        self.text_box.bind("<MouseWheel>", self._on_wheel)
        self.text_box.bind("<Button-3>", self._show_context_menu)
        self.text_box.bind("<Control-z>", self._do_undo)
        self.text_box.bind("<Control-y>", self._do_redo)
        self.text_box.bind("<Control-Shift-Z>", self._do_redo)
        self.text_box.bind("<Button-1>", self._on_click)
        self.text_box.bind("<B1-Motion>", self._on_drag)
        self.text_box.bind("<Control-c>", self._do_copy)
    
    def _on_wheel(self, event):
        """滚轮事件 - 调整字体大小"""
        if event.state & 0x0004:  # Ctrl
            self.text_font_size = max(8, min(32, self.text_font_size + (1 if event.delta > 0 else -1)))
            self.text_font.configure(size=self.text_font_size)
            return "break"
    
    def _show_context_menu(self, event):
        """显示右键菜单"""
        context_menu = tk.Menu(self.parent, tearoff=0)
        context_menu.post(event.x_root, event.y_root)
    
    def _do_undo(self, event=None):
        """撤销操作"""
        try:
            self.text_box.edit_undo()
        except tk.TclError:
            pass
        return "break"
    
    def _do_redo(self, event=None):
        """重做操作"""
        try:
            self.text_box.edit_redo()
        except tk.TclError:
            pass
        return "break"
    
    def _on_click(self, event):
        """Ctrl+左键选择列"""
        if event.state & 0x0004:  # 只有Ctrl+单击才处理列选择
            # 获取点击位置
            click_pos = self.text_box.index(f"@{event.x},{event.y}")
            line_num = int(click_pos.split('.')[0])
            
            # 获取点击行的文本
            line_text = self.text_box.get(f"{line_num}.0", f"{line_num}.end")
            columns = line_text.split('\t')
            
            # 计算列索引
            if event.x < 100:
                column_index = 0
            elif event.x < 200:
                column_index = 1
            elif event.x < 400:
                column_index = 2
            elif event.x < 600:
                column_index = 3
            else:
                column_index = 3
            
            # 记录选中的列索引
            self.selected_column_index = column_index
            
            # 清除之前的选择
            self.text_box.tag_remove(tk.SEL, "1.0", tk.END)
            
            # 选择整列
            for i in range(1, int(self.text_box.index('end-1c').split('.')[0]) + 1):
                line_text = self.text_box.get(f"{i}.0", f"{i}.end")
                columns = line_text.split('\t')
                if len(columns) > column_index:
                    # 计算列的起始和结束位置
                    start_pos = sum(len(columns[j]) + 1 for j in range(column_index))
                    end_pos = start_pos + len(columns[column_index])
                    self.text_box.tag_add(tk.SEL, f"{i}.{start_pos}", f"{i}.{end_pos}")
            
            return "break"
    
    def _on_drag(self, event):
        """普通拖动时重置列选择状态"""
        self.selected_column_index = None
    
    def _do_copy(self, event=None):
        """Ctrl+C 复制操作"""
        self._copy_selected_text()
        return "break"
    
    def _copy_selected_text(self):
        """复制选中的文本"""
        try:
            selected_text = self.text_box.get(tk.SEL_FIRST, tk.SEL_LAST)
            
            if selected_text:
                # 如果有记录的列索引，说明是列选择
                if self.selected_column_index is not None:
                    # 列选择：重新获取完整行数据，然后提取指定列
                    lines = selected_text.split('\n')
                    target_columns = []
                    
                    for i, line in enumerate(lines):
                        if line.strip():
                            # 重新获取完整行数据
                            line_num = i + 1  # 行号从1开始
                            full_line = self.text_box.get(f"{line_num}.0", f"{line_num}.end")
                            columns = full_line.split('\t')
                            
                            if len(columns) > self.selected_column_index:
                                target_columns.append(columns[self.selected_column_index])
                    
                    if target_columns:
                        result_text = '\n'.join(target_columns)
                        self.parent.clipboard_clear()
                        self.parent.clipboard_append(result_text)
                        return
                
                # 普通选择：复制用户实际选中的内容
                self.parent.clipboard_clear()
                self.parent.clipboard_append(selected_text)
                
        except Exception as e:
            error("复制失败", f"复制文本时出错: {str(e)}", parent=self.parent)
    
    def insert_text(self, text):
        """插入文本"""
        self.text_box.insert("1.0", text)
    
    def get_text(self):
        """获取文本内容"""
        return self.text_box.get("1.0", tk.END)
    
    def clear_text(self):
        """清空文本"""
        self.text_box.delete("1.0", tk.END)

