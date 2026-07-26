"""
湘西信息价 - 数据清洗与入库脚本
1. 从 parsed JSON 读取数据
2. 系统性地修复OCR错误
3. 去重、规范格式
4. 逐条入库
"""
import re
import json

# ============================================================
# 第一部分：OCR错误修复规则
# ============================================================

# 常见错字表
OCR_FIXES = {
    # 材料名称错字
    '热轧带勒': '热轧带肋',
    '热轧带勒盘螺': '热轧带肋盘螺',
    '热乳钢': '热轧工字钢',
    '热轧工字钢': '热轧工字钢',
    '热轧普通槽钢': '热轧普通槽钢',
    '热轧等边角钢': '热轧等边角钢',
    '热轧不等边角钢': '热轧不等边角钢',
    '热轧H型钢': '热轧H型钢',
    '热轧圆钢': '热轧圆钢',
    '热轧扁钢': '热轧扁钢',
    '热轧槽钢': '热轧槽钢',
    '混凝士': '混凝土',
    '商品混凝士': '商品混凝土',
    '沥青混凝士': '沥青混凝土',
    '预应力钢绞线': '预应力钢绞线',
    '无粘结预应力钢绞': '无粘结预应力钢绞线',
    '钢绞线、钢丝束': '钢绞线、钢丝束',
    '冷轧带肋钢筋': '冷轧带肋钢筋',
    '冷轧扭钢筋': '冷轧扭钢筋',
    '螺纹钢筋': '螺纹钢筋',
    '圆盘条': '圆盘条',
    '镀锌铁皮': '镀锌铁皮',
    '门窗用铝合金型材': '门窗用铝合金型材',
    '幕墙用铝合金型材': '幕墙用铝合金型材',
    '普通硅酸盐水泥': '普通硅酸盐水泥',
    '复合硅酸盐水泥': '复合硅酸盐水泥',
    '砌筑水泥': '砌筑水泥',
    '白水泥': '白水泥',
    '页岩烧结普通砖': '页岩烧结普通砖',
    '页岩烧结多孔砖': '页岩烧结多孔砖',
    '混凝土实心砖': '混凝土实心砖',
    '加气混凝土砌块': '加气混凝土砌块',
    '水泥彩瓦': '水泥彩瓦',
    '陶瓷瓦': '陶瓷瓦',
    '西班牙瓦': '西班牙瓦',
    '普通胶合板': '普通胶合板',
    '阻燃胶合板': '阻燃胶合板',
    '大芯板': '大芯板',
    '免漆板': '免漆板',
    '纸面石膏板': '纸面石膏板',
    '埃特板': '埃特板',
    '铝塑板': '铝塑板',
    '平板玻璃': '平板玻璃',
    '钢化玻璃': '钢化玻璃',
    '普通中空玻璃': '普通中空玻璃',
    '双钢化中空玻璃': '双钢化中空玻璃',
    '防火玻璃': '防火玻璃',
    '全瓷外墙砖': '全瓷外墙砖',
    '全瓷内墙砖': '全瓷内墙砖',
    '全瓷地砖': '全瓷地砖',
    'PVC塑料地板': 'PVC塑料地板',
    '氟碳喷涂铝单板': '氟碳喷涂铝单板',
    '铝扣板': '铝扣板',
    '彩钢装饰板': '彩钢装饰板',
    '彩钢板': '彩钢板',
    '彩钢夹芯板': '彩钢夹芯板',
    '不锈钢板': '不锈钢板',
    '粉末喷涂铝单板': '粉末喷涂铝单板',
    '断桥铝合金推拉': '断桥铝合金推拉门',
    '断桥铝合金平开': '断桥铝合金平开门',
    '断桥隔热平开窗': '断桥隔热平开窗',
    '断桥隔热推拉窗': '断桥隔热推拉窗',
    '普通铝合金推拉': '普通铝合金推拉窗',
    '普通铝合金平开': '普通铝合金平开门',
    '铝合金窗': '铝合金窗',
    '铝合金百叶窗': '铝合金百叶窗',
    '不锈钢压条': '不锈钢压条',
    '不锈钢角线': '不锈钢角线',
    '铝合金压条': '铝合金压条',
    '铝合金角线': '铝合金角线',
    '塑料压条': '塑料压条',
    '真石漆': '真石漆',
    '防水漆': '防水漆',
    '内墙漆': '内墙漆',
    '外墙乳胶漆': '外墙乳胶漆',
    '环氧漆': '环氧漆',
    '环氧富锌漆': '环氧富锌漆',
    '环氧红丹漆': '环氧红丹漆',
    '石油沥青': '石油沥青',
    '乳化沥青': '乳化沥青',
    '改性沥青': '改性沥青',
    '重交沥青': '重交沥青',
    '建筑油膏': '建筑油膏',
    '焊接钢管': '焊接钢管',
    '镀锌钢管': '镀锌钢管',
    '无缝钢管': '无缝钢管',
    'PE给水管': 'PE给水管',
    'PPR给水管': 'PPR给水管',
    'PVC-U排水管': 'PVC-U排水管',
    'HDPE双壁波纹管': 'HDPE双壁波纹管',
    'HDPE缠绕结构壁管': 'HDPE缠绕结构壁管',
    '球墨铸铁管': '球墨铸铁管',
    '镀锌玛钢管件': '镀锌玛钢管件',
    '沟槽管件': '沟槽管件',
    '消防沟槽管件': '消防沟槽管件',
    '消火栓箱': '消火栓箱',
    '灭火器': '灭火器',
    '环氧富锌底漆': '环氧富锌底漆',
    '环氧自流平面漆': '环氧自流平面漆',
    '环氧自流平中涂': '环氧自流平中涂',
    '环氧自流平底漆': '环氧自流平底漆',
    '钢结构防火涂料': '钢结构防火涂料',
    '球墨铸铁防盗雨水口篦子': '球墨铸铁防盗雨水口篦子',
    '球铁雨水篦子': '球铁雨水篦子',
    '球墨铸铁明沟盖板': '球墨铸铁明沟盖板',
    '人行道水泥彩砖': '人行道水泥彩砖',
    '透气渗水砖': '透气渗水砖',
    '彩色混凝土透水砖': '彩色混凝土透水砖',
    '井字形植草砖': '井字形植草砖',
    '花岗岩毛光板': '花岗岩毛光板',
    '装配式预制外挂': '装配式预制外挂板',
    '装配式贴砖预制外挂板': '装配式贴砖预制外挂板',
    '装配式预制梁下外墙': '装配式预制梁下外墙',
    '装配式预制梁下内墙': '装配式预制梁下内墙',
    '装配式预制内墙': '装配式预制内墙',
    '装配式预制女儿墙': '装配式预制女儿墙',
    '装配式预制楼梯': '装配式预制楼梯',
    '装配式预制叠合梁': '装配式预制叠合梁',
    '预制综合管廊': '预制综合管廊',
    '铜芯聚氯乙烯绝缘': '铜芯聚氯乙烯绝缘',
    '铜芯聚氯乙烯绝缘聚氯乙烯护套': '铜芯聚氯乙烯绝缘聚氯乙烯护套',
    '钢带增强聚乙烯(PE)螺旋波纹管': '钢带增强聚乙烯(PE)螺旋波纹管',
    '钢筋混凝土管': '钢筋混凝土管',
    '聚氯乙烯绝缘电线': '聚氯乙烯绝缘电线',
    '交联聚乙烯电力电缆': '交联聚乙烯电力电缆',
    '铝合金芯交联聚乙烯绝缘': '铝合金芯交联聚乙烯绝缘',
    '柔性矿物质绝缘电缆': '柔性矿物质绝缘电缆',
    '竹模板': '竹模板',
    '木模板': '木模板',
    '熟桐油': '熟桐油',
    
    # 单位错字
    'm²': 'm²',
    'm³': 'm³',
    'm²': 'm²',
    'm³': 'm³',
    'k': 'kg',
    'Ke': 'kg',
    'Ka': 'kg',
    '象': 'kg',
    '酒': 'kg',
    '商': 'kg',
    '文': 'kg',
    '电': 'm',
    '己': 'm',
    '中': 'm',
    '楼': 'm³',
    '换': 'm²',
    '国': 'm',
    '加': 'm',
    '日': 'm²',
    '品': 'm²',
    '康': 'm²',
    '适': 'm',
    '出': 'm³',
    '间': 'm',
    '麻': 'm²',
    '花': 'm²',
    '用': 'm',
    '司': '个',
    '出': 'm³',
    '强': '',
    '口': '',
    'x': '',
}

# 单位标准化映射
UNIT_NORMALIZE = {
    'kg': 'kg',
    'k': 'kg',
    'kg': 'kg',
    't': 't',
    'm': 'm',
    'm²': 'm²',
    'm³': 'm³',
    'm2': 'm²',
    'm3': 'm³',
    '块': '块',
    '个': '个',
    '套': '套',
    'km': 'km',
    '根': '根',
    '片': '片',
    '座': '座',
    '付': '付',
    '只': '只',
    '台': '台',
    '条': '条',
    '张': '张',
    '卷': '卷',
    '桶': '桶',
    '株': '株',
    '丛': '丛',
    '斤': '斤',
    '粒': '粒',
    '芽': '芽',
    '延米': '延米',
    'm/': 'm',
    'm²/': 'm²',
    'm³/': 'm³',
}


def clean_name(text):
    """清洗材料名称"""
    t = text
    
    # 应用OCR修复
    for wrong, correct in sorted(OCR_FIXES.items(), key=lambda x: -len(x[0])):
        t = t.replace(wrong, correct)
    
    # 去掉编码（长字母数字组合）
    t = re.sub(r'[A-Z0-9]{15,}', '', t)
    t = re.sub(r'[A-Z0-9]{10,}', '', t)
    
    # 去掉多余价格数字
    t = re.sub(r'\d+\.\d+', '', t)
    
    # 去掉单位
    for unit in ['kg', 'm²', 'm³', 'm', 't', '块', '个', '套', 'km', '根', '片', '座', '付', '只', '台', '条', '张', '卷', '桶', '株', '丛', '斤', '粒', '芽', '延米', 'k', 'g', '象', 'Ke', 'Ka', '酒', '商', '文', '电', '己', '中', '楼', '换', '国', '加', '日', '品', '康', '适', '出', '间', '麻', '花', '用', '司', '强', '口', 'x']:
        t = t.replace(unit, '')
    
    # 去掉多余空格和符号
    t = re.sub(r'[\(\)（）\[\]【】]', '', t)
    t = re.sub(r'\s+', ' ', t).strip()
    t = re.sub(r'[,，;；]+', '', t)
    
    # 去掉末尾的孤零零字符
    t = re.sub(r'\s+[^\w]\s*$', '', t)
    t = re.sub(r'^\s*[^\w]\s+', '', t)
    
    if not t or len(t) < 2:
        return None
    
    return t


def clean_unit(text):
    """提取并标准化单位"""
    # 先尝试直接匹配
    unit_patterns = [
        (r'\bkg\b', 'kg'),
        (r'\bkm\b', 'km'),
        (r'\bm³\b', 'm³'),
        (r'\bm²\b', 'm²'),
        (r'\bm\b', 'm'),
        (r'\bt\b', 't'),
        (r'\b块\b', '块'),
        (r'\b个\b', '个'),
        (r'\b套\b', '套'),
        (r'\b根\b', '根'),
        (r'\b片\b', '片'),
        (r'\b座\b', '座'),
        (r'\b付\b', '付'),
        (r'\b只\b', '只'),
        (r'\b台\b', '台'),
        (r'\b条\b', '条'),
        (r'\b张\b', '张'),
        (r'\b卷\b', '卷'),
        (r'\b桶\b', '桶'),
        (r'\b株\b', '株'),
        (r'\b丛\b', '丛'),
        (r'\b斤\b', '斤'),
        (r'\b粒\b', '粒'),
        (r'\b芽\b', '芽'),
        (r'\b延米\b', '延米'),
        (r'\b株\b', '株'),
    ]
    
    for pattern, unit in unit_patterns:
        if re.search(pattern, text):
            return unit
    
    return None


def clean_price(text):
    """提取价格对"""
    prices = re.findall(r'\d+\.\d+', text)
    if not prices:
        return None, None
    
    # 过滤不合理的价格（可能是年份、编号等）
    valid_prices = [p for p in prices if 0.01 <= float(p) <= 200000]
    
    if len(valid_prices) >= 2:
        return valid_prices[-2], valid_prices[-1]
    elif len(valid_prices) == 1:
        return valid_prices[0], valid_prices[0]
    return None, None


def clean_all(raw_json_path, output_path):
    """清洗所有数据"""
    with open(raw_json_path, 'r', encoding='utf-8') as f:
        all_data = json.load(f)
    
    cleaned = []
    errors = []
    
    for page, items in all_data.items():
        page_num = int(page)
        for item in items:
            raw = item['raw']
            unit = clean_unit(raw)
            p5, p6 = clean_price(raw)
            name = clean_name(raw)
            
            # 验证
            if not name or not unit or not p5 or not p6:
                errors.append({'page': page_num, 'raw': raw[:50], 'reason': f'name={name}, unit={unit}, p5={p5}, p6={p6}'})
                continue
            
            # 检查价格合理性
            p5_f, p6_f = float(p5), float(p6)
            if p5_f < 0.01 or p5_f > 200000:
                continue
            if p6_f < 0.01 or p6_f > 200000:
                continue
            
            # 去重
            key = f"{name}_{unit}_{p5}_{p6}"
            if any(c['key'] == key for c in cleaned):
                continue
            
            # 确定专业
            specialty = determine_specialty(name, page_num)
            
            cleaned.append({
                'key': key,
                'page': page_num,
                'name': name,
                'unit': unit,
                'price5': p5,
                'price6': p6,
                'specialty': specialty,
                'raw': raw[:80]
            })
    
    # 输出清洗结果
    print(f"原始数据: {sum(len(v) for v in all_data.values())} 条")
    print(f"清洗成功: {len(cleaned)} 条")
    print(f"清洗失败: {len(errors)} 条")
    print()
    
    # 按专业统计
    spec_counts = {}
    for c in cleaned:
        spec_counts[c['specialty']] = spec_counts.get(c['specialty'], 0) + 1
    
    print("按专业分布:")
    for spec, cnt in sorted(spec_counts.items()):
        print(f"  {spec}: {cnt} 条")
    print()
    
    # 按页统计
    page_counts = {}
    for c in cleaned:
        page_counts[c['page']] = page_counts.get(c['page'], 0) + 1
    print("按页分布:")
    for p in sorted(page_counts.keys()):
        print(f"  第{p}页: {page_counts[p]} 条")
    
    # 保存清洗结果
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'cleaned': [{k: v for k, v in c.items() if k != 'key'} for c in cleaned],
            'errors': errors
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n清洗结果已保存: {output_path}")
    print(f"错误日志: {len(errors)} 条")
    
    return cleaned, errors


def determine_specialty(name, page_num):
    """根据名称和页数判断专业"""
    # 根据页码
    if page_num in [21, 22]:
        return '土建'
    elif page_num in [23, 24, 25, 26, 27, 28, 29, 39]:
        return '土建'
    elif page_num in [30, 31, 38, 50, 51, 52, 53, 54]:
        return '市政'
    elif page_num in [32, 33, 34]:
        return '机电安装'
    elif page_num in [35, 36, 37, 55, 56, 57]:
        return '机电安装'
    elif page_num in [41, 42]:
        return '土建'
    elif page_num in [43, 44, 45, 46, 47, 48, 49]:
        return '园林景观'
    else:
        return '土建'  # 默认


if __name__ == '__main__':
    cleaned, errors = clean_all(
        'data/source/信息价_湘西/parsed/all_pages.json',
        'data/source/信息价_湘西/parsed/cleaned.json'
    )
    
    # 打印清洗错误示例
    if errors:
        print("\n清洗失败示例（前20条）:")
        for e in errors[:20]:
            print(f"  [第{e['page']}页] {e['raw']:<50} ➔ {e['reason']}")
    
    # 打印清洗成功示例
    print("\n清洗成功示例（前20条）:")
    for c in cleaned[:20]:
        print(f"  [第{c['page']}页] {c['name'][:45]:<45} | {c['unit']:<5} | {c['price5']:<8} | {c['price6']:<8} | {c['specialty']}")