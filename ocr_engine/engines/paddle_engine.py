"""
PaddleOCR引擎实现
"""
import gc
from core import lazy_import_numpy, lazy_import_paddleocr

class PaddleOCREngine:
    """PaddleOCR引擎"""
    
    def __init__(self):
        # 禁用OneDNN优化，避免兼容性问题
        import os
        os.environ['FLAGS_use_mkldnn'] = 'False'
        os.environ['FLAGS_use_cudnn'] = 'False'
        os.environ['FLAGS_use_gpu'] = 'False'
        
        # 延迟加载PaddleOCR
        PaddleOCR = lazy_import_paddleocr()
        if PaddleOCR is None:
            raise ImportError("PaddleOCR未安装，请运行: pip install paddleocr")
        
        # 初始化PaddleOCR，确保模型文件在正确位置
        import os
        import shutil
        
        # 获取项目根目录 - 修复路径计算
        current_file = __file__
        print(f"当前文件路径: {current_file}")
        
        # 从当前文件路径计算项目根目录
        # __file__ 是 ocr_engine/engines/paddle_engine.py
        # 需要回到项目根目录: ocr_engine/engines -> ocr_engine -> 项目根目录
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
        models_dir = os.path.join(base_dir, "models")
        
        print(f"计算的项目根目录: {base_dir}")
        print(f"计算的模型目录: {models_dir}")
        
        # 验证模型目录是否存在 - 多种路径查找策略
        if not os.path.exists(models_dir):
            print(f"[WARNING] 策略1失败，模型目录不存在: {models_dir}")
            
            # 策略2: 尝试使用当前工作目录
            cwd = os.getcwd()
            models_dir = os.path.join(cwd, "models")
            print(f"策略2 - 尝试使用工作目录: {models_dir}")
            
            # 策略3: 如果策略2也失败，尝试查找models目录
            if not os.path.exists(models_dir):
                print(f"[WARNING] 策略2失败，模型目录不存在: {models_dir}")
                # 在当前目录及其父目录中查找models目录
                search_dirs = [cwd]
                for i in range(3):  # 向上查找3层
                    parent = os.path.dirname(search_dirs[-1])
                    if parent != search_dirs[-1]:  # 避免无限循环
                        search_dirs.append(parent)
                
                models_dir = None
                for search_dir in search_dirs:
                    potential_models = os.path.join(search_dir, "models")
                    if os.path.exists(potential_models):
                        models_dir = potential_models
                        print(f"策略3 - 找到模型目录: {models_dir}")
                        break
                
                if not models_dir:
                    raise FileNotFoundError(f"无法找到模型目录，已尝试以下路径:\n- {os.path.join(base_dir, 'models')}\n- {os.path.join(cwd, 'models')}\n- 在 {search_dirs} 中搜索")
        
        # PaddleOCR期望的模型路径
        paddleocr_home = os.path.expanduser("~/.paddleocr/whl")
        
        # 如果项目中有模型文件，复制到PaddleOCR期望的位置
        if os.path.exists(models_dir):
            if not os.path.exists(paddleocr_home):
                os.makedirs(paddleocr_home, exist_ok=True)
            
            # 复制模型文件
            for model_type in ["det", "rec", "cls"]:
                src_path = os.path.join(models_dir, model_type)
                dst_path = os.path.join(paddleocr_home, model_type)
                if os.path.exists(src_path) and not os.path.exists(dst_path):
                    shutil.copytree(src_path, dst_path)
        
        # 初始化PaddleOCR，明确指定模型路径
        det_model_path = os.path.join(models_dir, "det", "ch", "ch_PP-OCRv4_det_infer")
        rec_model_path = os.path.join(models_dir, "rec", "ch", "ch_PP-OCRv4_rec_infer")
        cls_model_path = os.path.join(models_dir, "cls", "ch_ppocr_mobile_v2.0_cls_infer")
        
        # 验证模型文件是否存在
        print(f"检测模型路径: {det_model_path}")
        print(f"识别模型路径: {rec_model_path}")
        print(f"分类模型路径: {cls_model_path}")
        
        if not os.path.exists(os.path.join(det_model_path, "inference.pdmodel")):
            raise FileNotFoundError(f"检测模型文件不存在: {det_model_path}")
        if not os.path.exists(os.path.join(rec_model_path, "inference.pdmodel")):
            raise FileNotFoundError(f"识别模型文件不存在: {rec_model_path}")
        if not os.path.exists(os.path.join(cls_model_path, "inference.pdmodel")):
            raise FileNotFoundError(f"分类模型文件不存在: {cls_model_path}")
        
        self.ocr = PaddleOCR(
            use_angle_cls=True, 
            lang='ch',
            use_gpu=False,
            show_log=False,
            use_space_char=True,
            det_model_dir=det_model_path,
            rec_model_dir=rec_model_path,
            cls_model_dir=cls_model_path
        )
        
        # 模型预热：用一张小图片预热模型，提升首次识别速度
        try:
            np = lazy_import_numpy()
            if np is not None:
                dummy_img = np.ones((100, 100, 3), dtype=np.uint8) * 255
                self.ocr.ocr(dummy_img)
                pass  # 静默处理
        except Exception as e:
            pass  # 静默处理错误
    
    def recognize(self, image):
        """识别图片文字"""
        np = lazy_import_numpy()
        if np is None:
            raise ImportError("numpy未安装，请运行: pip install numpy")
        
        try:
            img_np = np.array(image)
            results = self.ocr.ocr(img_np)
            
            if not results or not results[0]:
                return []
            
            # 处理OCR结果
            blocks = []
            for line in results[0]:
                if line and len(line) >= 2:
                    box = line[0]
                    text = line[1][0]
                    x = np.mean([point[0] for point in box])
                    y = np.mean([point[1] for point in box])
                    blocks.append({'text': text, 'x': x, 'y': y})
            
            # 按坐标重组文本行
            result = self._reorganize_lines(blocks)
            
            # 清理临时变量
            del img_np, results, blocks
            
            return result
            
        finally:
            # 强制垃圾回收
            gc.collect()
    
    def _reorganize_lines(self, blocks):
        """重组文本行"""
        # 按y排序，分行
        blocks.sort(key=lambda b: b['y'])
        lines = []
        current_line = []
        last_y = None
        y_threshold = 10
        
        for b in blocks:
            if last_y is None or abs(b['y'] - last_y) < y_threshold:
                current_line.append(b)
            else:
                lines.append(current_line)
                current_line = [b]
            last_y = b['y']
        
        if current_line:
            lines.append(current_line)
        
        # 每行内容直接拼接
        text_lines = []
        for line in lines:
            line_sorted = sorted(line, key=lambda b: b['x'])
            line_text = ''.join([b['text'] for b in line_sorted])
            text_lines.append(line_text)
        
        return text_lines
    
    def get_engine_name(self):
        return "PaddleOCR"