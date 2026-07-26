
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

OCR_URL = "http://127.0.0.1:1224/api/ocr"
SOURCE_FILE = "湘西自治州工程造价_总第160期_2025年5-6月.pdf_OCR"
REGION = "湘西吉首"

# ============================================================
# AI知识库：根据OCR识别的文本推断正确的材料名称
# 这些是已知的OCR常见错误，以及对应的正确名称
# ============================================================
AI_KNOWLEDGE = {}

def build_knowledge():
    global AI_KNOWLEDGE
    # 钢筋类
    AI_KNOWLEDGE['热轧圆盘条（高'] = '热轧圆盘条（高线）'
    AI_KNOWLEDGE['热轧带勒'] = '热轧带肋'
    AI_KNOWLEDGE['热轧带肋盘螺'] = '热轧带肋盘螺'
    AI_KNOWLEDGE['HRB40OE'] = 'HRB400E'
    AI_KNOWLEDGE['HRB10QE'] = 'HRB400E'
    AI_KNOWLEDGE['热乳钢'] = '热轧工字钢'
    AI_KNOWLEDGE['3lkg'] = 'kg'
    AI_KNOWLEDGE['Ke'] = 'kg'
    AI_KNOWLEDGE['Ka'] = 'kg'
    AI_KNOWLEDGE['象'] = ''
    AI_KNOWLEDGE['酒'] = ''
    AI_KNOWLEDGE['商'] = ''
    AI_KNOWLEDGE['文'] = ''
    AI_KNOWLEDGE['中'] = ''
    AI_KNOWLEDGE['电'] = ''
    AI_KNOWLEDGE['己'] = ''
    AI_KNOWLEDGE['国'] = ''
    AI_KNOWLEDGE['加'] = ''
    AI_KNOWLEDGE['间'] = ''
    AI_KNOWLEDGE['出'] = ''
    AI_KNOWLEDGE['楼'] = 'm³'
    AI_KNOWLEDGE['换'] = ''
    AI_KNOWLEDGE['日'] = ''
    AI_KNOWLEDGE['品'] = ''
    AI_KNOWLEDGE['麻'] = ''
    AI_KNOWLEDGE['花'] = ''
    AI_KNOWLEDGE['司'] = ''
    AI_KNOWLEDGE['强'] = ''
    AI_KNOWLEDGE['口'] = ''
    AI_KNOWLEDGE['x'] = ''
    # 材料名
    AI_KNOWLEDGE['混凝士'] = '混凝土'
    AI_KNOWLEDGE['无粘结预应力钢绞'] = '无粘结预应力钢绞线'
    AI_KNOWLEDGE['硼筑水泥'] = '砌筑水泥'
    AI_KNOWLEDGE['m30'] = 'M30'
    AI_KNOWLEDGE['m²'] = 'm²'
    AI_KNOWLEDGE['m³'] = 'm³'
    AI_KNOWLEDGE['m2'] = 'm²'
    AI_KNOWLEDGE['m3'] = 'm³'

def ai_identify_unit(text):
    u = re.search(r'(kg|m²|m³|m|t|块|个|套|km|根|片|座|付|只|台|条|张|卷|桶|株|丛|斤|粒|芽|延米|m2|m3)', text)
    return u.group(1).replace('m2','m²').replace('m3','m³') if u else ''

def ai_identify_price(text):
    prices = re.findall(r'\d+\.\d+', text)
    valid = [p for p in prices if 0.01 <= float(p) <= 200000]
    if len(valid) >= 2: return valid[-2], valid[-1]
    if len(valid) == 1: return valid[0], valid[0]
    return None, None

def ai_clean_name(text):
    t = text
    # 应用知识库
    build_knowledge()
    for wrong, correct in sorted(AI_KNOWLEDGE.items(), key=lambda x: -len(x[0])):
        t = t.replace(wrong, correct)
    # 去掉编码
    t = re.sub(r'[A-Z0-9]{15,}', '', t)
    t = re.sub(r'[A-Z0-9]{10,}', '', t)
    # 去掉价格数字
    t = re.sub(r'\d+\.\d+', '', t)
    # 去掉残存单位
    t = re.sub(r'(kg|m²|m³|m|t|块|个|套|km|根|片|座|付|只|台|条|张|卷|桶|株|丛|斤|粒|芽|延米|m2|m3|m30|M30|k|Kg|Ke|Ka|g|象|酒|商|文|电|己|国|加|间|出|楼|换|日|品|麻|花|司|强|口|x|中|用|麻|花|康|适|麻|花|用|司|出|强|口|x|l)', '', t)
    # 清理
    t = re.sub(r'\s+', ' ', t).strip()
    t = t.strip('-–—×*/()（）【】. ')
    if not t or len(t) < 2: return None
    return t

def determine_specialty(page_num, name):
    if page_num in [21,22,23,24,25,26,27,28,39]: return '土建'
    if page_num in [29,30,31,38,50,51,52,53,54]: return '市政'
    if page_num in [32,33,34,35,36,37,55,56,57]: return '机电安装'
    if page_num in [41,42]: return '土建' if '水泥' in name or '砖' in name else '市政'
    if page_num in [43,44,45,46,47,48,49]: return '园林景观'
    return '土建'

def main():
    print("=" * 60)
    print("湘西信息价 - AI智能识别入库")
    print("=" * 60)

    with open('data/source/信息价_湘西/parsed/all_pages.json', 'r', encoding='utf-8') as f:
        all_data = json.load(f)

    all_items = []
    for page_str in sorted(all_data.keys(), key=lambda x: int(x)):
        page_num = int(page_str)
        items = all_data[page_str]
        if not items: continue
        page_items = []
        for item in items:
            raw = item['raw']
            p5, p6 = ai_identify_price(raw)
            if not p5 or not p6: continue
            unit = ai_identify_unit(raw)
            name = ai_clean_name(raw)
            if not name: continue
            page_items.append({
                'name': name, 'unit': unit,
                'price5': p5, 'price6': p6,
                'page': page_num,
                'specialty': determine_specialty(page_num, name)
            })
        all_items.extend(page_items)
        print(f"第{page_num}页: {len(page_items)}条")

    # 去重
    seen = set()
    unique = []
    for item in all_items:
        key = f"{item['name']}_{item['unit']}_{item['price5']}"
        if key not in seen:
            seen.add(key)
            unique.append(item)

    print(f"
总计: {len(unique)}条 (去重前{len(all_items)}条)")

    # 入库
    db = SessionLocal()
    db.execute(text("DELETE FROM t_price_unit WHERE source_file = :s"), {'s': SOURCE_FILE})
    db.commit()

    count = 0
    for item in unique:
        spec_id = db.execute(text("SELECT id FROM t_specialty WHERE name = :n"), {'n': item['specialty']}).scalar()
        if not spec_id: continue
        price_str = f"{item['price5']} / {item['price6']}" if item['price5'] != item['price6'] else item['price5']
        db.execute(text("""INSERT INTO t_price_unit (specialty_id, item_name, unit, price, region, source_file, remark) VALUES (:sid, :name, :unit, :price, :region, :source, :remark)"""), {
            'sid': spec_id, 'name': item['name'], 'unit': item['unit'] if item['unit'] else '-',
            'price': price_str, 'region': REGION, 'source': SOURCE_FILE,
            'remark': f"第{item['page']}页 OCR+AI识别"
        })
        count += 1

    db.commit()
    db.close()
    print(f"✅ 入库{count}条")

if __name__ == "__main__":
    main()
