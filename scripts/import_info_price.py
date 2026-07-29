"""
信息价导入脚本 - 从解析的JSON数据写入数据库t_region_info_price表
"""
import json
import sqlite3
import re
from datetime import datetime

DB_PATH = 'data/sqlite/工程助手.db'
JSON_PATH = 'data/source/信息价_湘西/parsed/all_pages.json'

def clean_item_name(raw: str) -> str:
    """从原始文本中提取物料名称"""
    # 去掉末尾的价格数字
    s = raw.strip()
    # 去掉末尾的数字/小数
    s = re.sub(r'\s+[\d.]+$', '', s)
    # 去掉末尾的kg/m/m²等单位
    s = re.sub(r'\s+(kg|m|m²|m³|t|个|块|片|根|套|只|条|台)$', '', s)
    # 去掉空括号
    s = re.sub(r'\s*[（(][\s]*[）)]', '', s)
    # 清理多余空格
    s = re.sub(r'\s+', ' ', s).strip()
    # 去掉编码前缀
    s = re.sub(r'^[A-Z0-9]+\s+', '', s)
    return s[:200] if s else raw[:200]

def clean_price(val) -> float:
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0

def import_data():
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        pages = json.load(f)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 清空旧数据
    cur.execute('DELETE FROM t_region_info_price')
    
    total = 0
    for page_num, items in pages.items():
        if not isinstance(items, list):
            continue
        for item in items:
            raw = item.get('raw', '')
            if not raw:
                continue
            # 跳过页眉页脚
            if len(raw) < 5:
                continue
            if '湘西自治州' in raw or '造价管理' in raw or '第' in raw and '期' in raw:
                continue
            if '供应价' in raw or '信息价' in raw or '材料名称' in raw:
                continue

            name = clean_item_name(raw)
            if not name or len(name) < 2:
                continue

            unit = item.get('unit', '')
            price5 = clean_price(item.get('price5', 0))
            price6 = clean_price(item.get('price6', 0))
            # 取5月价，如果没有则用6月价
            price = price5 if price5 > 0 else price6
            if price <= 0:
                continue

            cur.execute(
                'INSERT INTO t_region_info_price (region, period, item_name, unit, price, source_file, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
                ('湘西州', '2025年5-6月', name, unit, price,
                 '2025-3湘西(5、6月)(信息价).pdf', datetime.now().isoformat())
            )
            total += 1

    conn.commit()
    conn.close()
    print(f'✅ 导入完成: {total} 条信息价数据')

if __name__ == '__main__':
    import_data()