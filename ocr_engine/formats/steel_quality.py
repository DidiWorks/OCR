"""
缺陷质量格式
"""
"""
钢铁质量格式（坐标驱动 + 轻分类 + 流式横排）
- 批号：纯数字（默认10位）
- 牌号：大写开头，后续大写/数字/符号 + - /
- 卷号：11位，首尾字母
- 输入既可为OCR坐标项列表，也可为纯文本行
- 输出：每行一条记录 → "卷号 坯号 牌号 问题"
"""
import re
import statistics
from typing import List, Dict, Any, Tuple

# ------------------------
# 坐标工具
# ------------------------
def _box_cx(box): 
    return statistics.mean([p[0] for p in box])
def _box_cy(box): 
    return statistics.mean([p[1] for p in box])

def _cluster_rows(items: List[Dict[str, Any]], y_threshold: int = 10) -> List[List[Dict[str, Any]]]:
    """按 y 坐标聚类为行"""
    items_sorted = sorted(items, key=lambda it: _box_cy(it["box"]))
    rows, cur, last_y = [], [], None
    for it in items_sorted:
        cy = _box_cy(it["box"])
        if last_y is None or abs(cy - last_y) <= y_threshold:
            cur.append(it)
            last_y = cy if last_y is None else (last_y + cy) / 2.0
        else:
            rows.append(cur)
            cur = [it]
            last_y = cy
    if cur:
        rows.append(cur)
    return rows

def _row_to_tokens(row: List[Dict[str, Any]]) -> List[str]:
    """保留旧接口：仅返回分词后的文本序列（按x排序）"""
    return [t for t, _ in _row_to_tokens_with_x(row)]

def _row_to_tokens_with_x(row: List[Dict[str, Any]]) -> List[Tuple[str, float]]:
    """行内按x排序，并做深度分词，返回 (token, cx) 用于列聚类"""
    row_sorted = sorted(row, key=lambda it: _box_cx(it["box"]))
    fine: List[Tuple[str, float]] = []
    for it in row_sorted:
        t = str(it.get("text", "")).strip()
        if not t:
            continue
        cx = _box_cx(it["box"])  # 同一原token的子片段用微偏移保持相对次序
        parts = _split_mixed_token(t)
        if not parts:
            continue
        step = 0.0001
        base = cx - (len(parts) - 1) * step / 2.0
        for idx, p in enumerate(parts):
            fine.append((p, base + idx * step))
    return fine

def _cluster_columns_by_x(tokens_with_x: List[Tuple[str, float]], x_gap: float) -> List[List[str]]:
    """基于x间隔的自适应列聚类：x间距大于阈值则断列"""
    if not tokens_with_x:
        return []
    items = sorted(tokens_with_x, key=lambda x: x[1])
    cols: List[List[str]] = []
    cur: List[str] = []
    last_x: float = None
    for tok, cx in items:
        if last_x is None or abs(cx - last_x) <= x_gap:
            cur.append(tok)
        else:
            cols.append(cur)
            cur = [tok]
        last_x = cx
    if cur:
        cols.append(cur)
    return cols

def _build_records_from_columns(cols: List[List[str]]) -> List[Tuple[str, str, str, str]]:
    """按列（从左到右）提取字段；在同一列内可连续抽取多个字段，并移除已用片段。"""
    juan = ""; pi = ""; pai = ""; issue_parts: List[str] = []

    def take_from_col(col: List[str], pattern: re.Pattern, max_span: int) -> Tuple[str, List[str]]:
        # 单token优先
        for i, t in enumerate(col):
            if pattern.fullmatch(t):
                return t, col[:i] + col[i+1:]
        # 相邻拼接（最多 max_span）
        n = len(col)
        for span in range(2, min(max_span, n) + 1):
            for i in range(n - span + 1):
                combo = ''.join(col[i:i+span])
                if pattern.fullmatch(combo):
                    return combo, col[:i] + col[i+span:]
        return "", col

    for col in cols:
        working = col[:]
        progressed = True
        # 在同一列中，按顺序尽可能抽取多个字段
        while progressed and working:
            progressed = False
            if not juan:
                cand, working2 = take_from_col(working, JUAN_RE, 6)
                if cand:
                    juan = cand; working = working2; progressed = True; continue
            if not pi:
                # 先严格纯数字10位
                cand, working2 = take_from_col(working, PI_STRICT_RE, 4)
                # 特例：单个数字片段长度>10，切出前10位作为批号，其余回填
                if not cand:
                    for idx, tok in enumerate(working):
                        if tok.isdigit() and len(tok) > 10:
                            cand = tok[:10]
                            rest_tail = tok[10:]
                            working2 = working[:idx] + ([rest_tail] if rest_tail else []) + working[idx+1:]
                            break
                if not cand:
                    # 再容错：拼接成10位后，数字>=9且字母<=1
                    n = len(working)
                    found = ""; new_work = working
                    for span in range(2, min(6, n) + 1):
                        for i in range(n - span + 1):
                            combo = ''.join(working[i:i+span])
                            if len(combo) == 10 and PI_LEN10_RE.fullmatch(combo):
                                digits = sum(ch.isdigit() for ch in combo)
                                letters = sum('A' <= ch <= 'Z' for ch in combo)
                                if digits >= 9 and letters <= 1:
                                    found = combo
                                    new_work = working[:i] + working[i+span:]
                                    break
                        if found:
                            break
                    cand, working2 = found, new_work
                    if cand and _is_debug_enabled_mod():
                        _debug_mod("batch_fallback", cand)
                if cand:
                    pi = cand; working = working2; progressed = True; continue
            if not pai:
                cand, working2 = take_from_col(working, PAI_RE, 8)
                if cand:
                    pai = cand; working = working2; progressed = True; continue
        # 剩余作为问题：仅做边界断开与长度限制
        if working:
            raw_issue = ' '.join(working)
            raw_issue = _insert_issue_boundaries(raw_issue)
            raw_issue = _limit_issue_length(raw_issue, 40)
            issue_parts.append(raw_issue)

    issue = ' '.join([p for p in issue_parts if p]).strip()
    # 清理牌号：去除空格
    pai_cleaned = _clean_paihao(pai)
    rec = (juan, pi, pai_cleaned, issue)
    return [rec] if any(rec) else []

# ------------------------
# 字段判定（依据你的明确规则）
# ------------------------
# 卷号：10-12位，首尾都是字母（更宽松）
JUAN_RE = re.compile(r'^[A-Za-z][A-Za-z0-9]{8,10}[A-Za-z]$')
# 批号：更宽松的规则
# - 严格：纯数字10位
# - 容错：10位字母数字组合
PI_STRICT_RE = re.compile(r'^\d{10}$')
PI_LEN10_RE  = re.compile(r'^[A-Z0-9]{10}$')
# 新增：包含字母的10-14位组合（支持更长的批号）
PI_MIXED_RE = re.compile(r'^[A-Z0-9]{10,14}$')
# 牌号：更宽松的规则，匹配各种牌号格式
# 示例：SS37、DC53D+Z、SPHC-S、HC340/590DPD+Z、DC01、SPCC2
PAI_RE  = re.compile(r'^[A-Za-z0-9+\-\/\s]{2,16}$')

def _clean_paihao(pai: str) -> str:
    """清理牌号：智能处理各种格式"""
    if not pai:
        return pai
    
    # 去除首尾空格
    cleaned = pai.strip()
    
    # 特殊处理：如果包含中文，说明不是牌号，返回原值
    if re.search(r'[\u4e00-\u9fa5]', cleaned):
        return cleaned
    
    # 去除空格，但保留特殊符号
    cleaned = re.sub(r'\s+', '', cleaned)
    
    # 确保至少包含一个字母
    if not re.search(r'[A-Za-z]', cleaned):
        return pai  # 如果没有字母，返回原值
    
    return cleaned

def _classify_token(tok: str) -> str:
    t = tok.strip()
    
    # 如果包含中文，直接归为问题
    if re.search(r'[\u4e00-\u9fa5]', t):
        return "问题"
    
    # 卷号：11位字母数字组合
    if JUAN_RE.fullmatch(t): 
        return "卷号"
    
    # 批号：10位数字
    if PI_STRICT_RE.fullmatch(t):   
        return "坯号"
    
    # 牌号：包含字母的短字符串
    if PAI_RE.fullmatch(t) and re.search(r'[A-Za-z]', t) and len(t) <= 16:
        return "牌号"
    
    return "问题"  # 其它统一归"问题"

def _build_records_from_tokens(tokens: list[str]) -> list[tuple[str,str,str,str]]:
    """简单直接的字段识别"""
    if not tokens:
        return []
    
    # 清理所有token
    clean_tokens = [t.strip() for t in tokens if t.strip()]
    if not clean_tokens:
        return []
    
    # 简单策略：按顺序识别字段
    juan = ""
    pi = ""
    pai = ""
    issue_parts = []
    
    # 寻找卷号（字母开头11位）
    for i, token in enumerate(clean_tokens):
        if JUAN_RE.fullmatch(token):
            juan = token
            clean_tokens.pop(i)
            break
    
    # 寻找批号（10-14位数字或字母数字）
    for i, token in enumerate(clean_tokens):
        if (PI_STRICT_RE.fullmatch(token) or PI_MIXED_RE.fullmatch(token)):
            pi = token
            clean_tokens.pop(i)
            break
    
    # 寻找牌号（字母开头，不包含中文）
    for i, token in enumerate(clean_tokens):
        if (PAI_RE.fullmatch(token) and re.search(r'[A-Za-z]', token) and not re.search(r'[\u4e00-\u9fa5]', token)):
            pai = token
            clean_tokens.pop(i)
            break
    
    # 剩余所有token作为问题
    issue = " ".join(clean_tokens).strip()
    
    # 至少要有卷号或批号
    if not juan and not pi:
        return []
    
    # 返回记录
    rec = (juan, pi, pai, issue)
    return [rec]

# ------------------------
# 深度分词：将混合token切成字母段/数字段/符号段/中文段
# ------------------------
_DEEP_SPLIT_RE = re.compile(r'[A-Z]+|\d+|[+\-/]+|[\u4e00-\u9fa5]+')
_NOISE_CHARS = set(list('、】〔〕[]{}()<>“”‘’`~!@#$%^&*_=?\\|,:;…'))

def _split_mixed_token(tok: str) -> List[str]:
    """简化分词：直接按空格分割"""
    s = tok.strip().replace('：', ':').replace('，', ',').replace('；', ';')
    
    # 直接按空格分割
    parts = [part.strip() for part in s.split() if part.strip()]
    
    # 过滤纯噪声符号
    out = []
    for part in parts:
        if not all(ch in _NOISE_CHARS for ch in part):
            out.append(part)
    
    return out if out else [s]

# ------------------------
# 问题边界与长度控制（仅作用于“问题”文本，不影响字段匹配）
# ------------------------
_ASCII_PIECE = r'[A-Za-z0-9+\-/]'
_CJK = r'[\u4e00-\u9fa5]'

def _insert_issue_boundaries(text: str) -> str:
    if not text:
        return text
    s = text
    # ASCII 与 中文相邻处断开
    s = re.sub(rf'({_ASCII_PIECE})({_CJK})', r'\1 \2', s)
    s = re.sub(rf'({_CJK})({_ASCII_PIECE})', r'\1 \2', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def _limit_issue_length(text: str, max_len: int = 40) -> str:
    if not text:
        return text
    return text[:max_len]

# ------------------------
# 问题文本构建：多信号判定 + 清洗合并
# ------------------------
_CN_RE = re.compile(r'[\u4e00-\u9fa5]')
_NUM_UNIT_RE = re.compile(r'\d+(?:\.\d+)?\s*(?:mm|cm|m|米|张|件|%)', re.IGNORECASE)
_CMP_RE = re.compile(r'(?:>=|<=|>|<|≈|±)\s*\d+(?:\.\d+)?\s*(?:mm|cm|m|米|%)?', re.IGNORECASE)

def _has_cn(s: str) -> bool:
    return bool(_CN_RE.search(s))

def _is_issue_token(tok: str) -> bool:
    t = tok.strip()
    if not t:
        return False
    # 保护牌号片段：形如 [A-Z0-9+\-/] 且包含至少1个大写字母的ASCII段，不纳入问题
    if PAI_RE.fullmatch(t):
        return False
    # 同时保护大小写字母混合的ASCII片段（至少含1个字母）
    if re.fullmatch(r'(?=.*[A-Za-z])[A-Za-z0-9+\-/]{2,}', t):
        return False
    if _has_cn(t):
        return True
    if _NUM_UNIT_RE.fullmatch(t) or _CMP_RE.fullmatch(t):
        return True
    return False

def _beautify_issue(text: str, max_total_len: int = 50) -> str:
    # 在中文与数字/符号之间插入空格，简单归一比较表达
    s = re.sub(r'([\u4e00-\u9fa5])([0-9])', r'\1 \2', text)
    s = re.sub(r'([0-9])([\u4e00-\u9fa5])', r'\1 \2', s)
    s = re.sub(r'\s+', ' ', s).strip()
    if len(s) > max_total_len:
        s = s[:max_total_len]
    return s

def _build_issue_from_tokens(tokens: List[str]) -> str:
    # 过滤噪声：仅中文/比较/数值单位/关键词（后续可接入关键词）
    # 简化：先按判定条件挑选，再直接拼接
    parts: List[str] = []
    for t in tokens:
        if _is_issue_token(t):
            parts.append(t)
    if not parts:
        return ""
    return _beautify_issue(' '.join(parts))
        
# ------------------------
# 纯文本行的顺序提取（兼容卷号缺失）
# ------------------------
PAT_JUANHAO = re.compile(r'([A-Za-z][A-Za-z0-9]{10})(.*)')                # 与你原式兼容（11位总长）
# 保留占位，不再直接用宽松正则提批号，转为基于token的严格+容错判定
PAT_PIHAO   = re.compile(r'(\d{10})(.*)')
PAT_PAIHAO  = re.compile(r'((?=[A-Z0-9+\-/]{2,30}$)(?=.*[A-Z])[A-Z0-9+\-/]+)(.*)')  # 至少含一位大写字母

def _normalize_line(s: str) -> str:
    s = s.replace('：', ':')
    s = re.sub(r'[，、；;|,:]+', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def _extract_fields_plain(line: str) -> str:
    """
    
    - 卷号可缺失（找不到不早退）
    - 批号：先严格10位纯数字；失败再容错（总长10，数字>=9 字母<=1）
    - 牌号=大写开头 + [A-Z0-9+\-/]
    """
    rest = line.strip()

    # 先取卷号（与原始顺序一致）
    m1 = PAT_JUANHAO.match(rest)
    if m1:
        juan = m1.group(1)
        rest = m1.group(2).strip()
    else:
        # 尝试修复首字母错误：0开头的情况
        # 情况1：0 + 10位数字 + 字母 + 剩余
        m1_fixed = re.match(r'^0(\d{10})([A-Za-z])(.*)', rest)
        if m1_fixed:
            juan = 'Q' + m1_fixed.group(1) + m1_fixed.group(2)
            rest = m1_fixed.group(3).strip()
        else:
            # 情况2：0 + 10位数字 + 剩余（没有尾字母）
            m1_fixed2 = re.match(r'^0(\d{10})(.*)', rest)
            if m1_fixed2:
                juan = 'Q' + m1_fixed2.group(1)
                rest = m1_fixed2.group(2).strip()
            else:
                # 情况3：0 + 9位数字 + 字母 + 剩余（11位总长度）
                m1_fixed3 = re.match(r'^0(\d{9})([A-Za-z])(.*)', rest)
                if m1_fixed3:
                    juan = 'Q' + m1_fixed3.group(1) + m1_fixed3.group(2)
                    rest = m1_fixed3.group(3).strip()
                else:
                    juan = "" 
                    rest = rest.strip()   


    # 对剩余串做深度分词，按相邻拼接寻找批号（严格→容错）
    tokens = _DEEP_SPLIT_RE.findall(rest)
    tokens = [t for t in tokens if t and t.strip()]

    # 批号严格：纯数字10位
    pi = ""; pi_end_idx = -1
    n = len(tokens)
    # 先尝试单token严格
    for i, t in enumerate(tokens):
        # 先尝试严格匹配
        if PI_STRICT_RE.fullmatch(t):
            pi = t; pi_end_idx = i; break
        
        # 容错：尝试修复中间字母错误
        if len(t) == 10 and t.isdigit():
            pi = t; pi_end_idx = i; break
        elif len(t) == 10 and t[0].isdigit() and t[-1].isdigit():
            # 中间可能有字母，尝试修复
            fixed_t = re.sub(r'[A-Za-z]', '0', t)
            if PI_STRICT_RE.fullmatch(fixed_t):
                pi = fixed_t; pi_end_idx = i; break
    # 先检查是否有超长数字需要切分
    if not pi:
        for i, t in enumerate(tokens):
            if t.isdigit() and len(t) > 10:
                # 超长数字，强制切分：前10位作为批号，剩余作为牌号
                pi = t[:10]
                pi_end_idx = i
                # 把剩余部分作为新的token插入
                remaining = t[10:]
                if remaining:
                    tokens.insert(i+1, remaining)
                    n = len(tokens)  # 更新tokens长度
                break
    
    # 如果还没有找到批号，继续原来的逻辑
    if not pi:
        # 容错：总长10-14，且仅[A-Z0-9]，数字>=9 字母<=1
        for span in range(1, min(6, n) + 1):
            found = False
            for i in range(n - span + 1):
                combo = ''.join(tokens[i:i+span])
                if PI_MIXED_RE.fullmatch(combo):
                    digits = sum(ch.isdigit() for ch in combo)
                    letters = sum('A' <= ch <= 'Z' for ch in combo)
                    if digits >= 9 and letters <= 1:
                        pi = combo; pi_end_idx = i + span - 1; found = True; break
            if found:
                break

    if not pi:
        # return f"{juan}\t\t{rest}".strip()
        return f"{juan}\t\t\t{rest}".strip()

    # # 检测：卷号缺失但批号是10位数字（可能是卷号首字母被OCR略过）
    # if not juan and pi and pi.isdigit() and len(pi) == 10:
    #     juan = "[⚠️卷号缺失]"
    
    # 牌号：在批号之后的剩余串里匹配
    if 'rest_after_pi' not in locals():
        rest_after_pi = ''.join(tokens[pi_end_idx+1:]).strip()

    # 先分离完整的牌号和问题
    pai = ""
    issue_after_pai = ""

    for i, char in enumerate(rest_after_pi):
        if char.isascii() and not char.isspace():
            pai += char
        else:
            # 遇到中文或空格，后面的都是问题
            issue_after_pai = rest_after_pi[i:].strip()
            break

    # 如果没找到分界点，整个都是牌号
    if not issue_after_pai:
        pai = rest_after_pi
        issue_after_pai = ""

    # 牌号列：牌号 + 空格填充到20位
    pai_padded = pai.ljust(16)


    # 问题列：单独问题
    issue_after_pai = _limit_issue_length(_insert_issue_boundaries(issue_after_pai), 40)

    # 输出4列格式：卷号、批号、牌号(20位)、问题
    return "\t".join([juan, pi, pai_padded, issue_after_pai]).strip()



    # m3 = PAI_RE.match(rest_after_pi)
    # if m3:
    #     pai = m3.group(0)
    #     rest3 = rest_after_pi[len(pai):].strip()
    #     rest3 = _limit_issue_length(_insert_issue_boundaries(rest3), 40)
    #     # 输出制表符分隔，保证"问题"列对齐
    #     return "\t".join([juan, pi, pai, rest3]).strip()
    # else:
    #     rest_after_pi = _limit_issue_length(_insert_issue_boundaries(rest_after_pi), 40)
    #     # 统一4列格式：卷号、坯号、牌号(空)、问题
    #     return "\t".join([juan, pi, "", rest_after_pi]).strip()

# ------------------------
# 主处理器
# ------------------------
class SteelQualityFormat:
    DEFAULT_Y_THRESHOLD = 10  # 行聚类容差

    def process(self, items_or_lines):
        """
        - 若传入为 OCR 坐标项列表（含 box/text），按坐标分行横排 + 轻分类构建记录
        - 若传入为纯文本行列表，使用顺序提取（卷号可缺）
        返回：多行字符串，每行："卷号 坯号 牌号 问题"
        """
        if not items_or_lines:
            return "没有找到有效记录"
        
        # OCR坐标流
        if isinstance(items_or_lines[0], dict) and "box" in items_or_lines[0]:
            y_th = self._read_y_threshold()
            rows = _cluster_rows(items_or_lines, y_threshold=y_th)
            all_records: List[Tuple[str, str, str, str]] = []
            x_gap = self._read_x_gap()
            for r in rows:
                toks_x = _row_to_tokens_with_x(r)
                if self._is_debug_enabled():
                    self._debug("row_tokens:", [(t, round(x,2)) for t,x in toks_x])
                cols = _cluster_columns_by_x(toks_x, x_gap=x_gap)
                if self._is_debug_enabled():
                    self._debug("cols:", [" ".join(c) for c in cols])
                recs = _build_records_from_columns(cols)
                if self._is_debug_enabled():
                    for juan, pi, pai, issue in recs:
                        self._debug("hit:", juan, pi, pai, issue)
                all_records.extend(recs)
            lines = ["\t".join(rec) for rec in all_records]
            return "\n".join(lines) if lines else "没有找到有效记录"

        # 纯文本行
        out = []
        for raw in items_or_lines:
            line = _normalize_line(str(raw or ""))
            if not line:
                continue
            out.append(_extract_fields_plain(line))
        return "\n".join(out) if out else "没有找到有效记录"

    def _read_y_threshold(self) -> int:
        """从设置读取 y_threshold（找不到用默认）"""
        try:
            from ocr_engine.config import load_config
            cfg = load_config() or {}
            return int(cfg.get("ocr", {}).get("y_threshold", self.DEFAULT_Y_THRESHOLD))
        except Exception:
            return self.DEFAULT_Y_THRESHOLD

    def _read_x_gap(self) -> float:
        """从设置读取列分隔阈值（像素/坐标单位），默认40"""
        try:
            from ocr_engine.config import load_config
            cfg = load_config() or {}
            return float(cfg.get("ocr", {}).get("x_col_gap", 40))
        except Exception:
            return 40.0

    def _is_debug_enabled(self) -> bool:
        return _is_debug_enabled_mod()

    def _debug(self, *args):
        _debug_mod(*args)
    
    def get_format_name(self):
        return "steel_quality_v1"

# 模块级调试工具，便于在非类作用域调用
def _is_debug_enabled_mod() -> bool:
    try:
        from ocr_engine.config import load_config
        cfg = load_config() or {}
        ocr_dbg = bool(cfg.get("ocr", {}).get("debug_format", False))
        sq_dbg = bool(cfg.get("debug", {}).get("steel_quality", False))
        return ocr_dbg or sq_dbg
    except Exception:
        return False

def _debug_mod(*args):
    try:
        if _is_debug_enabled_mod():
            print("[steel_quality]", *args)
    except Exception:
        pass
