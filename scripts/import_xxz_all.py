"""
湘西信息价 - 最终入库脚本
使用坐标OCR重建表格，清洗后入库
"""
import sys
sys.path.insert(0, '.')

import requests
import base64
import re
import json
import os
from collections import defaultdict
from packages.server.db.database import SessionLocal
from sqlalchemy import text

OCR_URL = 'http://127.0.0.1:1224/api/ocr'
SOURCE_FILE = "湘西自治州工程造价_总第160期_2025年5-6月.pdf"
REGION = "湘西吉首"

# ============================================================
# OCR修复字典
# ============================================================
OCR_FIXES = {
    # 材料名
    '热轧带勒': '热轧带肋', '热乳钢': '热轧工字钢', '热轧工字钢': '热轧工字钢',
    '热轧普通槽钢': '热轧普通槽钢', '热轧等边角钢': '热轧等边角钢', '热轧不等边角钢': '热轧不等边角钢',
    '热轧H型钢': '热轧H型钢', '热轧圆钢': '热轧圆钢', '热轧扁钢': '热轧扁钢',
    '热轧槽钢': '热轧槽钢', '钢筋': '钢筋', '盘螺': '盘螺', '圆盘条': '圆盘条',
    '螺纹钢筋': '螺纹钢筋', '冷轧带肋钢筋': '冷轧带肋钢筋', '冷轧扭钢筋': '冷轧扭钢筋',
    '预应力钢绞线': '预应力钢绞线', '无粘结预应力钢绞': '无粘结预应力钢绞线',
    '镀锌铁皮': '镀锌铁皮', '铝合金型材': '铝合金型材', '幕墙': '幕墙', '门窗': '门窗',
    '焊条': '焊条', '安全网': '安全网', '镀锌铁丝': '镀锌铁丝', '镀锌钢丝网': '镀锌钢丝网',
    '铁件': '铁件', '彩条布': '彩条布', '耐碱玻璃纤维': '耐碱玻璃纤维',
    '水泥': '水泥', '砂子': '砂子', '碎石': '碎石', '石屑': '石屑', '石灰': '石灰',
    '毛石': '毛石', '砖': '砖', '砌块': '砌块', '瓦': '瓦',
    '混凝士': '混凝土', '商品混凝士': '商品混凝土', '沥青混凝士': '沥青混凝土',
    '透水混凝士': '透水混凝土', '森林材料': '胶合板', '胶合板': '胶合板',
    '埃特板': '埃特板', '铝塑板': '铝塑板', '石膏板': '石膏板', '免漆板': '免漆板',
    '大芯板': '大芯板', '玻璃': '玻璃', '钢化玻璃': '钢化玻璃', '中空玻璃': '中空玻璃',
    '防火玻璃': '防火玻璃', '外墙砖': '外墙砖', '内墙砖': '内墙砖', '地砖': '地砖',
    '不锈钢板': '不锈钢板', '彩钢板': '彩钢板', '彩钢夹芯板': '彩钢夹芯板',
    '铝单板': '铝单板', '铝扣板': '铝扣板',
    '真石漆': '真石漆', '乳胶漆': '乳胶漆', '防火涂料': '防火涂料',
    '环氧富锌': '环氧富锌', '环氧自流平': '环氧自流平', '钢结构防火涂料': '钢结构防火涂料',
    '焊接钢管': '焊接钢管', '镀锌钢管': '镀锌钢管', '无缝钢管': '无缝钢管',
    'PE给水管': 'PE给水管', 'PPR给水管': 'PPR给水管', 'PVC-U排水管': 'PVC-U排水管',
    'HDPE双壁波纹管': 'HDPE双壁波纹管', 'HDPE缠绕结构壁管': 'HDPE缠绕结构壁管',
    '球墨铸铁管': '球墨铸铁管', '镀锌玛钢管件': '镀锌玛钢管件', '沟槽管件': '沟槽管件',
    '消火栓箱': '消火栓箱', '灭火器': '灭火器',
    '球墨铸铁防盗': '球墨铸铁防盗', '雨水篦子': '雨水篦子', '井盖': '井盖',
    '植草砖': '植草砖', '透水砖': '透水砖', '路缘石': '路缘石', '平石': '平石',
    '花岗岩': '花岗岩',
    '装配式预制': '装配式预制', '竹模板': '竹模板', '木模板': '木模板',
    '铜芯聚氯乙烯': '铜芯聚氯乙烯', '电力电缆': '电力电缆', '控制电缆': '控制电缆',
    '聚氯乙烯绝缘电线': '聚氯乙烯绝缘电线', '交联聚乙烯': '交联聚乙烯',
    '矿物质绝缘电缆': '矿物质绝缘电缆',
    '熟桐油': '熟桐油', '石油沥青': '石油沥青', '乳化沥青': '乳化沥青',
    '改性沥青': '改性沥青', '重交沥青': '重交沥青',
    '镀锌钢管': '镀锌钢管', '衬塑钢管': '衬塑钢管', '涂塑钢管': '涂塑钢管',
    'PP-R管': 'PP-R管', 'PE-RT管': 'PE-RT管', 'PB管': 'PB管',
    '检查井': '检查井', '化粪池': '化粪池', '隔油池': '隔油池',
    '阀门': '阀门', '水表': '水表', '消火栓': '消火栓',
    '钢带增强聚乙烯(PE)螺旋波纹管': '钢带增强聚乙烯(PE)螺旋波纹管',
    '钢筋混凝土管': '钢筋混凝土管',
    '保温材料': '保温材料', '挤塑板': '挤塑板', '聚苯板': '聚苯板',
    '岩棉板': '岩棉板', '玻璃棉': '玻璃棉',
    '防水卷材': '防水卷材', '防水涂料': '防水涂料',
    'SBS改性沥青': 'SBS改性沥青', 'APP改性沥青': 'APP改性沥青',
    '种植土': '种植土', '草皮': '草皮', '苗木': '苗木',
    '春鹃': '春鹃', '夏鹃': '夏鹃', '四季桂': '四季桂',
    '香樟': '香樟', '桂花': '桂花', '银杏': '银杏',
    '红叶石楠': '红叶石楠', '金森女贞': '金森女贞',
    '红花继木': '红花继木', '金边黄杨': '金边黄杨',
    '麦冬': '麦冬', '玉龙草': '玉龙草', '吉祥草': '吉祥草',
    '紫藤': '紫藤', '凌霄': '凌霄', '爬山虎': '爬山虎',
    
    # 单位错字
    'k': 'kg', 'Kg': 'kg', 'Ke': 'kg', 'Ka': 'kg', '象': 'kg', '酒': 'kg',
    '商': 'kg', '文': 'kg', '中': 'm', '电': 'm', '己': 'm', '国': 'm',
    '加': 'm', '间': 'm', '用': 'm', '楼': 'm³', '换': 'm²', '日': 'm²',
    '品': 'm²', '麻': 'm²', '花': 'm²', '司': '个', '出': 'm³', '麻': 'm²',
    '花': 'm²', '用': 'm', '司': '个', '出': 'm³', '强': '', '口': '',
    'x': '', 'l': '', '': '',
}

UNIT_MAP = {
    'kg': 'kg', 'k': 'kg', 'Kg': 'kg', 'Ke': 'kg', 'Ka': 'kg',
    't': 't',
    'm': 'm', 'm²': 'm²', 'm³': 'm³', 'm2': 'm²', 'm3': 'm³',
    'km': 'km',
    '块': '块', '个': '个', '套': '套', '根': '根', '片': '片',
    '座': '座', '付': '付', '只': '只', '台': '台', '条': '条',
    '张': '张', '卷': '卷', '桶': '桶', '株': '株', '丛': '丛',
    '斤': '斤', '芽': '芽', '粒': '粒', '延米': '延米',
}

SPECIALTY_MAP = {
    # 页码 -> 专业
    21: '市政', 22: '市政', 23: '土建', 24: '土建', 25: '土建', 26: '土建', 27: '土建',
    28: '土建', 29: '市政', 30: '市政', 31: '市政', 32: '机电安装', 33: '机电安装',
    34: '机电安装', 35: '机电安装', 36: '机电安装', 37: '土建', 38: '市政', 39: '土建',
    41: '土建', 42: '市政', 43: '园林景观', 44: '园林景观', 45: '园林景观',
    46: '园林景观', 47: '园林景观', 48: '园林景观', 49: '园林景观',
    50: '市政', 51: '市政', 52: '市政', 53: '市政', 54: '市政',
    55: '机电安装', 56: '机电安装', 57: '机电安装',
}


def ocr_page(page_num, parser='single_line'):
    """OCR识别，返回带坐标的文字块"""
    img_path = f'data/source/信息价_湘西/images/page_{page_num}.png'
    if not os.path.exists(img_path):
        return None
    
    with open(img_path, 'rb') as f:
        img_base64 = base64.b64encode(f.read()).decode('utf-8')
    
    r = requests.post(OCR_URL, json={
        'base64': img_base64,
        'options': {
            'ocr.language': 'models/config_chinese.txt',
            'ocr.maxSideLen': 960,
            'tbpu.parser': parser,
            'data.format': 'dict'
        }
    }, timeout=120)
    res = r.json()
    return res.get('data', []) if res.get('code') == 100 else None


def split_columns(blocks):
    """自动分栏"""
    xs = [(b['box'][0][0] + b['box'][2][0]) / 2 for b in blocks]
    sorted_xs = sorted(xs)
    max_gap, split_x = 0, (sorted_xs[0] + sorted_xs[-1]) / 2
    for i in range(len(sorted_xs) - 1):
        gap = sorted_xs[i+1] - sorted_xs[i]
        if gap > max_gap:
            max_gap, split_x = gap, (sorted_xs[i] + sorted_xs[i+1]) / 2
    left, right = [], []
    for b in blocks:
        x = (b['box'][0][0] + b['box'][2][0]) / 2
        (left if x < split_x else right).append(b)
    return left, right


def group_rows(blocks, tol=15):
    groups = defaultdict(list)
    for b in blocks:
        y = (b['box'][0][1] + b['box'][2][1]) / 2
        groups[round(y / tol) * tol].append(b)
    rows = []
    for y in sorted(groups):
        items = sorted(groups[y], key=lambda b: b['box'][0][0])
        text = ' '.join(b['text'] for b in items).strip()
        if text:
            rows.append((y, text))
    return rows


def merge_entries(rows):
    """合并相邻行成完整条目"""
    skip_words = ['编码', '名称', '规格', '单位', '单价', '5月', '6月', '材料市场',
                  '复印无效', '获取', '扫描', '微信', 'WWW', 'http', '总第', '吉首',
                  '注：', '篇码', '口', '强', '电', '己', 'x']
    
    data_rows = [(y, t) for y, t in rows if t and len(t) >= 2 and not any(s in t for s in skip_words) and not re.match(r'^\d+$', t.strip())]
    
    # 合并：把没有价格的行合并到最近的有价格行
    merged = []
    i = 0
    while i < len(data_rows):
        y, text = data_rows[i]
        prices = re.findall(r'\d+\.\d+', text)
        
        if prices:
            merged.append((y, text))
            i += 1
        else:
            # 向前合并直到有价格
            parts = [text]
            j = i + 1
            while j < len(data_rows):
                y2, t2 = data_rows[j]
                if re.findall(r'\d+\.\d+', t2):
                    parts.append(t2)
                    merged.append((y, ' '.join(parts)))
                    i = j + 1
                    break
                else:
                    parts.append(t2)
                    j += 1
            else:
                i = j
    
    return merged


def clean_item(text, page_num):
    """清洗单条数据"""
    # 应用OCR修复
    for wrong, correct in sorted(OCR_FIXES.items(), key=lambda x: -len(x[0])):
        text = text.replace(wrong, correct)
    
    # 提取价格
    prices = re.findall(r'\d+\.\d+', text)
    if not prices:
        return None
    
    # 取最后一个价格对
    p5 = p6 = prices[0]
    if len(prices) >= 2:
        p5, p6 = prices[-2], prices[-1]
    
    p5f, p6f = float(p5), float(p6)
    if p5f < 0.01 or p5f > 200000:
        return None
    if p6f < 0.01 or p6f > 200000:
        return None
    
    # 提取单位
    unit = ''
    for pat, u in sorted(UNIT_MAP.items(), key=lambda x: -len(x[0])):
        if pat in ('k', 'x', 'l', '') and len(pat) < 2:
            continue
        if re.search(r'\b' + re.escape(pat) + r'\b', text):
            unit = u
            break
    
    if not unit:
        # 在文本中找单位
        unit_match = re.search(r'\b(kg|m²|m³|m|t|块|个|套|km|根|片|座|付|只|台|条|张|卷|桶|株|丛|斤|粒|芽|延米)\b', text)
        if unit_match:
            unit = unit_match.group(1)
    
    # 清理名称
    clean = text
    clean = re.sub(r'[A-Z0-9]{15,}', '', clean)
    clean = re.sub(r'[A-Z0-9]{10,}', '', clean)
    clean = re.sub(r'\d+\.\d+', '', clean)
    clean = re.sub(r'\b(kg|m²|m³|m|t|块|个|套|km|根|片|座|付|只|台|条|张|卷|桶|株|丛|斤|粒|芽|延米|k|Kg|Ke|Ka|m2|m3)\b', '', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()
    clean = re.sub(r'^[\s\-–—×*/()（）【】.]+', '', clean)
    clean = re.sub(r'[\s\-–—×*/()（）【】.]+$', '', clean)
    
    if not clean or len(clean) < 2:
        return None
    
    return {
        'name': clean[:60],
        'unit': unit,
        'price5': p5,
        'price6': p6,
        'page': page_num,
        'specialty': SPECIALTY_MAP.get(page_num, '土建')
    }


def process_page(page_num):
    """处理单页"""
    blocks = ocr_page(page_num)
    if not blocks:
        return []
    
    left, right = split_columns(blocks)
    all_items = []
    
    for col in [left, right]:
        rows = group_rows(col)
        entries = merge_entries(rows)
        for y, text in entries:
            item = clean_item(text, page_num)
            if item:
                all_items.append(item)
    
    return all_items


def insert_to_db(items):
    """入库到数据库"""
    db = SessionLocal()
    
    # 先清空该来源的旧数据
    db.execute(text("DELETE FROM t_price_unit WHERE source_file = :s"), {'s': SOURCE_FILE})
    db.commit()
    
    count = 0
    for item in items:
        spec_id = db.execute(
            text("SELECT id FROM t_specialty WHERE name = :n"),
            {'n': item['specialty']}
        ).scalar()
        
        if not spec_id:
            print(f"  [WARN] 专业不存在: {item['specialty']}")
            continue
        
        # 去重检查
        exists = db.execute(text("""
            SELECT id FROM t_price_unit 
            WHERE item_name = :name AND unit = :unit AND price LIKE :price
            AND region = :region
        """), {
            'name': item['name'],
            'unit': item['unit'],
            'price': f"%{item['price5']}%",
            'region': REGION
        }).fetchone()
        
        if exists:
            continue
        
        db.execute(text("""
            INSERT INTO t_price_unit 
            (specialty_id, item_name, unit, price, region, source_file, remark)
            VALUES (:sid, :name, :unit, :price, :region, :source, :remark)
        """), {
            'sid': spec_id,
            'name': item['name'],
            'unit': item['unit'],
            'price': f"{item['price5']} / {item['price6']}",
            'region': REGION,
            'source': SOURCE_FILE,
            'remark': f"第{item['page']}页 OCR识别，已清洗"
        })
        count += 1
    
    db.commit()
    db.close()
    return count


# ============================================================
# 主流程
# ============================================================
if __name__ == '__main__':
    print("=" * 60)
    print("湘西信息价 - 完整导入")
    print("=" * 60)
    
    # 需要处理的页面（跳过已手动处理过的40、50、58）
    pages = [21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39,
             41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57]
    
    all_items = []
    for page in pages:
        items = process_page(page)
        all_items.extend(items)
        print(f"第{page}页: {len(items)}条")
    
    # 去重
    seen = set()
    unique_items = []
    for item in all_items:
        key = f"{item['name']}_{item['unit']}_{item['price5']}_{item['price6']}"
        if key not in seen:
            seen.add(key)
            unique_items.append(item)
    
    print(f"\n📊 总计: {len(unique_items)} 条 (去重后)")
    print(f"   原始: {len(all_items)} 条")
    
    # 按专业统计
    spec_counts = defaultdict(int)
    for item in unique_items:
        spec_counts[item['specialty']] += 1
    print("\n按专业:")
    for spec, cnt in sorted(spec_counts.items()):
        print(f"  {spec}: {cnt} 条")
    
    # 入库
    print("\n正在入库...")
    inserted = insert_to_db(unique_items)
    print(f"✅ 入库完成: {inserted} 条")
    
    # 验证
    db = SessionLocal()
    total = db.execute(text("SELECT COUNT(*) FROM t_price_unit WHERE source_file = :s"), {'s': SOURCE_FILE}).scalar()
    db.close()
    print(f"📌 数据库总数: {total} 条")
    print(f"📌 来源: {SOURCE_FILE}")