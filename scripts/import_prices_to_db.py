r"""
造价通 - 价格信息库 .md 批量导入 SQLite
读取 H:\AI-model\价格信息库\ 下的 13 个 .md 文件，解析为结构化记录入库

- 8 个专业速查表 → t_price_unit (17,944 条)
- 1 个市政重点专题 → t_topic_price (370 条)
- 1 个省市信息价主线表 → t_region_info_price (主线表是目录索引,真正的价格数据待 M5 解析 PDF/Excel)
- 1 个规费措施税金费率表 → t_fee_rate (各地费率)
- 1 个综合单价分析模板 → 不入数据库,作为参考文档

注：信息价主线表是"目录索引",真正价格数据需要后续解析各地 PDF/xlsx。
本脚本只把结构化已提炼的导入。
"""
import re
import sys
import json
from pathlib import Path
from typing import List, Dict, Tuple

# 项目根(造价通/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from packages.server.db.database import SessionLocal, init_db
from packages.server.db.models import (
    Specialty, PriceUnit, TopicPrice, RegionInfoPrice, FeeRate
)


# 8 大专业速查表映射
SPECIALTY_FILES = [
    ("土建", "土建_综合单价速查表.md"),
    ("市政", "市政_综合单价速查表.md"),
    ("机电安装", "机电安装_综合单价速查表.md"),
    ("装饰装修", "装饰装修_综合单价速查表.md"),
    ("园林景观", "园林景观_综合单价速查表.md"),
    ("门窗幕墙", "门窗幕墙_综合单价速查表.md"),
    ("钢结构", "钢结构_综合单价速查表.md"),
    ("涂料", "涂料_综合单价速查表.md"),
]

TOPIC_FILE = "市政/重点专题_管道基坑钢板桩.md"

# 主题映射(与 filter_municipal.py 一致)
TOPIC_SECTIONS = [
    "管道铺设与修复",
    "深基坑开挖与支护",
    "钢板桩",
    "降水工程",
    "桩基与地基处理",
]


def parse_md_table(md_text: str) -> List[Dict]:
    """
    解析 markdown 表格, 返回 dict 列表
    表头列名: 序号 | 项目名称 | 单位 | 综合单价(元) | 计量规则 | 备注 | 来源
    """
    rows = []
    lines = md_text.split("\n")
    headers = None
    for line in lines:
        line = line.strip()
        if not line.startswith("|"):
            continue
        # 跳过分隔行 |---|---|
        if re.match(r"^\|[\s:\-|]+\|?$", line):
            continue
        # 跳过 ">" 引用块
        if line.startswith("> "):
            continue

        parts = [p.strip() for p in line.split("|")]
        # 去除首尾空字符串
        parts = parts[1:-1] if len(parts) >= 2 and parts[0] == "" and parts[-1] == "" else parts

        if not parts:
            continue

        # 第一行是表头
        if headers is None:
            # 过滤掉"序号"开头的行(可能是数据行,我们要找含"项目名称"的表头)
            if "项目名称" in " ".join(parts):
                headers = parts
                continue
            # 跳过非表头
            continue

        # 数据行
        if len(parts) != len(headers):
            continue

        # 序号必须是数字
        if not re.match(r"^\d+$", parts[0].strip()):
            continue

        row = dict(zip(headers, parts))
        rows.append(row)

    return rows


def parse_topic_md(md_text: str) -> List[Dict]:
    """解析市政重点专题表(分主题归档)"""
    rows = []
    current_topic = None
    headers = None
    lines = md_text.split("\n")

    for line in lines:
        # 章节检测
        m = re.match(r"^## (.+?)$", line)
        if m:
            topic_name = m.group(1).strip()
            if topic_name in TOPIC_SECTIONS:
                current_topic = topic_name
                headers = None
                continue
            else:
                current_topic = None
                continue

        if current_topic is None:
            continue

        line = line.strip()
        if not line.startswith("|"):
            continue
        if re.match(r"^\|[\s:\-|]+\|?$", line):
            continue
        if line.startswith("> "):
            continue

        parts = [p.strip() for p in line.split("|")]
        parts = parts[1:-1] if len(parts) >= 2 and parts[0] == "" and parts[-1] == "" else parts

        if not parts:
            continue

        if headers is None:
            if "项目名称" in " ".join(parts):
                headers = parts
                continue
            continue

        if len(parts) != len(headers):
            continue
        if not re.match(r"^\d+$", parts[0].strip()):
            continue

        row = dict(zip(headers, parts))
        row["__topic__"] = current_topic
        rows.append(row)

    return rows


def import_specialty_prices(session) -> Tuple[int, int]:
    """导入 8 个专业速查表 → t_price_unit"""
    total_inserted = 0
    specialty_count = 0

    for spec_name, filename in SPECIALTY_FILES:
        fp = PROJECT_ROOT.parent / "价格信息库" / spec_name / filename
        if not fp.exists():
            print(f"  [WARN] 文件不存在: {fp}")
            continue

        # 创建专业记录(如不存在)
        specialty = session.query(Specialty).filter_by(name=spec_name).first()
        if not specialty:
            specialty = Specialty(name=spec_name, code=spec_name, description=f"{spec_name}专业综合单价")
            session.add(specialty)
            session.commit()
        specialty_count += 1

        # 解析 + 入库
        with open(fp, encoding="utf-8") as f:
            text = f.read()
        rows = parse_md_table(text)
        print(f"  [OK] {spec_name}: 解析 {len(rows)} 条")

        for r in rows:
            pu = PriceUnit(
                specialty_id=specialty.id,
                item_name=r.get("项目名称", "").strip(),
                unit=r.get("单位", "").strip(),
                price=r.get("综合单价（元）", r.get("综合单价(元)", "")).strip(),
                region="全国",
                calc_rule=r.get("计量规则", ""),
                remark=r.get("备注", ""),
                source_file=r.get("来源", ""),
            )
            session.add(pu)
            total_inserted += 1

        # 批量提交,每文件一次
        session.commit()

    return total_inserted, specialty_count


def import_topic_prices(session) -> int:
    """导入市政重点专题 → t_topic_price"""
    fp = PROJECT_ROOT.parent / "价格信息库" / "市政" / "重点专题_管道基坑钢板桩.md"
    if not fp.exists():
        print(f"  [WARN] 文件不存在: {fp}")
        return 0

    with open(fp, encoding="utf-8") as f:
        text = f.read()
    rows = parse_topic_md(text)
    print(f"  [OK] 市政重点专题: 解析 {len(rows)} 条")

    for r in rows:
        tp = TopicPrice(
            topic=r["__topic__"],
            item_name=r.get("项目名称", "").strip(),
            unit=r.get("单位", "").strip(),
            price=r.get("综合单价（元）", r.get("综合单价(元)", "")).strip(),
            calc_rule=r.get("计量规则", ""),
            remark=r.get("备注", ""),
            source_file=r.get("来源", ""),
        )
        session.add(tp)

    session.commit()
    return len(rows)


def import_fee_rates_from_md(session) -> int:
    """
    从规费措施税金费率表提取已表格化的费率

    规费_措施费_税金费率表.md 中的"全国通用安全文明施工费率"是区间,
    信息价配套的实际费率需要后续从各地 PDF 解析,这里只导入示例数据。
    """
    # 示例数据 - 后续从 PDF 批量解析补充
    sample_rates = [
        ("全国", "税金", "增值税(一般计税)", 0.09, "分部分项+措施+其他+规费", "国家统一"),
        ("全国", "税金", "增值税(简易计税)", 0.03, "税前造价", "国家统一"),
        ("北京市", "规费", "规费合计", 0.2183, "分部分项合计", "22.北京市造价信息价"),
        ("上海市", "规费", "规费合计", 0.2712, "分部分项合计", "23.上海市造价信息价"),
        ("天津市", "规费", "规费合计", 0.2598, "分部分项合计", "24.天津市造价信息价"),
        ("重庆市", "规费", "规费合计", 0.2755, "分部分项合计", "21.重庆市造价信息价"),
        ("广东省", "规费", "规费合计", 0.2705, "分部分项合计", "25.广东省造价信息价"),
        ("浙江省", "规费", "规费合计", 0.2451, "分部分项合计", "26.浙江省造价信息价"),
        ("江苏省", "规费", "规费合计", 0.2600, "分部分项合计", "27.江苏省造价信息价"),
        # 安全文明施工费率典型值
        ("北京市", "措施费", "安全文明施工", 0.0346, "分部分项+措施+其他", "全国参考表"),
        ("上海市", "措施费", "安全文明施工", 0.0341, "分部分项+措施+其他", "全国参考表"),
        ("天津市", "措施费", "安全文明施工", 0.0325, "分部分项+措施+其他", "全国参考表"),
        ("重庆市", "措施费", "安全文明施工", 0.0350, "分部分项+措施+其他", "全国参考表"),
        ("广东省", "措施费", "安全文明施工", 0.0316, "分部分项+措施+其他", "全国参考表"),
        ("浙江省", "措施费", "安全文明施工", 0.0300, "分部分项+措施+其他", "全国参考表"),
        ("江苏省", "措施费", "安全文明施工", 0.0300, "分部分项+措施+其他", "全国参考表"),
    ]

    for r in sample_rates:
        fr = FeeRate(
            region=r[0], fee_type=r[1], fee_subitem=r[2],
            rate=r[3], calc_base=r[4], source_file=r[5],
            remark="M1 阶段示例数据,M6 后从各地信息价 PDF 批量解析"
        )
        session.add(fr)
    session.commit()
    return len(sample_rates)


def main():
    print("=" * 60)
    print("造价通 - 价格信息库导入 SQLite")
    print("=" * 60)

    print("\n[1/4] 初始化数据库(创建 14 张表)...")
    init_db()
    print("  [OK] 表结构创建完毕")

    print("\n[2/4] 导入 8 个专业速查表...")
    session = SessionLocal()
    try:
        total, spec_count = import_specialty_prices(session)
        print(f"  [OK] 共 {spec_count} 个专业, {total} 条价格入库")
    finally:
        session.close()

    print("\n[3/4] 导入市政重点专题...")
    session = SessionLocal()
    try:
        topic_total = import_topic_prices(session)
        print(f"  [OK] 共 {topic_total} 条专题入库")
    finally:
        session.close()

    print("\n[4/4] 导入规费措施费率(示例数据)...")
    session = SessionLocal()
    try:
        fee_total = import_fee_rates_from_md(session)
        print(f"  [OK] 共 {fee_total} 条费率入库")
    finally:
        session.close()

    print("\n" + "=" * 60)
    print("导入完毕。数据库位置:", PROJECT_ROOT / "data" / "sqlite" / "造价通.db")
    print("=" * 60)


if __name__ == "__main__":
    main()
