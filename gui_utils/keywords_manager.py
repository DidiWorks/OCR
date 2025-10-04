# 关键词管理器组件
# 从 compare_window.py 中提取的关键词管理功能

import tkinter as tk
import json
import os

class KeywordsManager:
    """关键词管理器组件"""
    
    def __init__(self, parent):
        self.parent = parent
        self.current_keywords = []
        self.config_path = "config/settings.json"
        self.highlight_callback = None  # 高亮更新回调
        self._load_keywords()
    
    def _load_keywords(self):
        """加载关键词"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    default = data.get('keywords', {}).get('default', [])
                    user_added = data.get('keywords', {}).get('user_added', [])
                    self.current_keywords = default + user_added
            else:
                self.current_keywords = ["卷取", "超宽", "上海"]
        except:
            self.current_keywords = ["卷取", "超宽", "上海"]
    
    def create_keywords_editor(self, parent_frame):
        """创建关键词编辑器"""
        # 标题行
        title_frame = tk.Frame(parent_frame)
        title_frame.pack(fill=tk.X, pady=(0, 5))
        
        tk.Label(title_frame, text="关键词:", font=("Arial", 10)).pack(side=tk.LEFT)
        
        # 编辑区域
        self.keywords_edit_area = tk.Text(parent_frame, height=8, font=("Arial", 9))
        self.keywords_edit_area.pack(fill=tk.X, pady=5)
        
        # 绑定事件
        self.keywords_edit_area.bind('<KeyRelease>', self._on_keywords_edit)
        self.keywords_edit_area.config(undo=True)  # 启用撤销功能
        self.keywords_edit_area.bind("<Control-z>", lambda e: self.keywords_edit_area.edit_undo())
        self.keywords_edit_area.bind("<Control-y>", lambda e: self.keywords_edit_area.edit_redo())
        
        # 初始化显示
        self._update_keywords_display()
        
        return self.keywords_edit_area
    
    def _update_keywords_display(self):
        """更新关键词显示"""
        self.keywords_edit_area.delete("1.0", tk.END)
        self.keywords_edit_area.insert("1.0", "\n".join(self.current_keywords))
    
    def _on_keywords_edit(self, event):
        """关键词编辑事件"""
        new_text = self.keywords_edit_area.get("1.0", tk.END).strip()
        new_keywords = [line.strip() for line in new_text.split('\n') if line.strip()]
        self.current_keywords.clear()
        self.current_keywords.extend(new_keywords)
        self._save_keywords()
        
        # 触发高亮更新
        if self.highlight_callback:
            self.highlight_callback(self.current_keywords)
    
    def _save_keywords(self):
        """保存关键词"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {'keywords': {'default': [], 'user_added': []}}
            
            data['keywords']['user_added'] = self.current_keywords
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            pass  # 静默处理错误
    
    def get_keywords(self):
        """获取当前关键词"""
        return self.current_keywords.copy()
    
    def set_keywords(self, keywords):
        """设置关键词"""
        self.current_keywords = keywords.copy()
        self._update_keywords_display()
        self._save_keywords()
    
    def add_keyword(self, keyword):
        """添加关键词"""
        if keyword not in self.current_keywords:
            self.current_keywords.append(keyword)
            self._update_keywords_display()
            self._save_keywords()
    
    def remove_keyword(self, keyword):
        """删除关键词"""
        if keyword in self.current_keywords:
            self.current_keywords.remove(keyword)
            self._update_keywords_display()
            self._save_keywords()
    
    def set_highlight_callback(self, callback):
        """设置高亮更新回调"""
        self.highlight_callback = callback
