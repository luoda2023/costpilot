"""
湘西信息价 - 材料价格表解析脚本
使用UmiOCR的dict格式（带坐标信息）重建表格结构
"""
import requests
import base64
import json
import os
import re
from collections import defaultdict

OCR_URL = 'http://127.0.0.1:1224/api/ocr'

def ocr_page(page_num, parser='single_line'):
    """OCR识别一页，返回带坐标的文字块"""
    img_path = f'data/source/信息价_湘西/images/page_{page_num}.png'
    if not os.path.exists(img_path):
        return None
    
    with open(img_path, 'rb') as f:
        img_base64 = base64.b64encode(f.read()).decode('utf-8')
    
    data = {
        'base64': img_base64,
        'options': {
            'ocr.angle': False,
            'ocr.language': 'models/config_chinese.txt',
            'ocr.maxSideLen': 960,
            'tbpu.parser': parser,
            'data.format': 'dict'
        }
    }
    
    r = requests.post(OCR_URL, json=data, timeout=120)
    result = r.json()
    if result.get('code') != 100:
        return None
    return result.get('data', [])


def split_columns(blocks, n_cols=2):
    """根据X坐标分栏（双栏布局）"""
    if not blocks:
        return []
    
    xs = [(b['box'][0][0] + b['box'][2][0]) / 2 for b in blocks]
    min_x, max_x = min(xs), max(xs)
    
    # 找左右栏的分界点（X坐标的中间gap）
    sorted_xs = sorted(xs)
    gaps = [(sorted_xs[i+1] - sorted_xs[i], i) for i in range(len(sorted_xs)-1)]
    biggest_gap = max(gaps, key=lambda x: x[0])
    split_x = (sorted_xs[biggest_gap[1]] + sorted_xs[biggest_gap[1]+1]) / 2
    
    cols = [[] for _ in range(n_cols)]
    for b in blocks:
        x_c = (b['box'][0][0] + b['box'][2][0]) / 2
        col_idx = min(int((x_c - min_x) / ((max_x - min_x) / n_cols)), n_cols-1)
        cols[col_idx].append(b)
    
    return cols


def group_into_rows(blocks, y_tolerance=15):
    """按Y坐标将文字块分组为行"""
    y_groups = defaultdict(list)
    for b in blocks:
        box = b['box']
        y_c = (box[0][1] + box[2][1]) / 2
        bucket = round(y_c / y_tolerance) * y_tolerance
        y_groups[bucket].append(b)
    
    rows = []
    for y in sorted(y_groups.keys()):
        items = sorted(y_groups[y], key=lambda b: (b['box'][0][0] + b['box'][2][0]) / 2)
        text = ' '.join(b['text'] for b in items)
        rows.append((y, text, items))
    
    return rows


def is_data_row(text, items):
    """判断一行是否是数据行（包含价格数字或编码）"""
    if not text.strip():
        return False
    # 跳过标题行
    keywords = ['编码', '名称', '规格', '单位', '单价', '材料市场', '复印无效',
                'WWW', '获取', '扫描', '微信', '总第', '吉首', '注：']
    for kw in keywords:
        if text.startswith(kw) or kw in text:
            return False
    # 跳过页码
    if re.match(r'^\d+$', text.strip()):
        return False
    if re.match(r'^[^\w]?$', text.strip()):
        return False
    return True


def extract_price_pairs(text):
    """从文本中提取价格对"""
    # 找类似 3.28 3.20 或 3.28 | 3.20 的价格对
    prices = re.findall(r'\d+\.\d+', text)
    # 取最后两个数字作为5月/6月单价
    if len(prices) >= 2:
        return prices[-2], prices[-1]
    elif len(prices) == 1:
        return prices[0], prices[0]
    return None, None


def parse_material_page(page_num, rows):
    """解析材料价格页的数据行"""
    items = []
    current_name = ''
    current_spec = ''
    current_unit = ''
    
    for y, text, blocks in rows:
        if not is_data_row(text, blocks):
            continue
        
        # 检查是否包含材料编码（数字+字母组合）
        has_code = bool(re.search(r'[A-Z0-9]{10,}', text))
        
        # 提取价格
        price5, price6 = extract_price_pairs(text)
        
        # 提取单位
        unit_match = re.search(r'\b(kg|m[²³]?|m|t|块|个|套|m²|m³)\b', text)
        unit = unit_match.group(1) if unit_match else ''
        
        # 提取规格
        spec_match = re.search(r'(HPB300|HRB400|Q235|CRB600|Φ\d+|@\d+|中\d+|\d+x\d+)', text)
        spec = spec_match.group(1) if spec_match else ''
        
        # 提取名称
        name_match = re.search(r'(热轧|螺纹|冷轧|预应力|钢绞线|无粘结)', text)
        name = name_match.group(1) if name_match else ''
        
        # 如果有编码，这行是完整的数据行
        if has_code or (price5 and name):
            items.append({
                'name': text[:40],
                'spec': spec,
                'unit': unit,
                'price5': price5,
                'price6': price6,
                'raw': text,
                'y': y
            })
    
    return items


def print_table(items, title=""):
    """打印表格供核对"""
    if title:
        print(f"\n{'='*70}")
        print(f"  {title}")
        print(f"{'='*70}")
    
    if not items:
        print("  (无数据)")
        return
    
    print(f"  {'名称':<30} {'规格':<15} {'单位':<6} {'5月':<10} {'6月':<10}")
    print(f"  {'-'*75}")
    for item in items[:30]:  # 最多显示30条
        name = item.get('name', '')[:28]
        spec = item.get('spec', '')[:13]
        unit = item.get('unit', '')[:4]
        p5 = item.get('price5', '') or '-'
        p6 = item.get('price6', '') or '-'
        print(f"  {name:<30} {spec:<15} {unit:<6} {p5:<10} {p6:<10}")
    
    if len(items) > 30:
        print(f"  ... 还有 {len(items)-30} 条")


# ============================================================
# 测试：处理第21页（钢筋）
# ============================================================
print("正在识别第21页...")
blocks = ocr_page(21)
if blocks:
    cols = split_columns(blocks)
    for i, col in enumerate(cols):
        rows = group_into_rows(col)
        items = parse_material_page(21, rows)
        print_table(items, f"第21页-第{i+1}栏 钢筋材料")
        print(f"  共提取 {len(items)} 条")
else:
    print("OCR失败")