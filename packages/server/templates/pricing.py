"""
造价通 - 报价组价算法

按 H:\\AI-model\\查询存档\\06_COST_COMPOSITION.md 的费用组成规则:
1. 综合单价(一类) = 材料费 + 人工费 + 机械费 + 管理费(5%) + 利润(5%) + 规费 + 税金(9%)
2. 二类(措施费) = 安全文明施工(3.5%) + 夜间施工 + 二次搬运 + 已完工程保护 + ... (按地区费率查 t_fee_rate)
3. 三类(其他) = 规费(以分部分项合计为基数 × 各地区费率) + 税金(一般计税9% / 简易计税3%)

支持 4 个阶段:
  - 估算: 单价用地区信息价 + 类似项目指标(平米/单位)
  - 概算: 单价用地区信息价 + 类似项目指标
  - 预算: 单价用综合单价库(t_price_unit)精确匹配
  - 结算: 单价按合同约定(可自定义 / 调差)
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from decimal import Decimal, ROUND_HALF_UP


# ---------------------------------------------------------------------------
# 数据类
# ---------------------------------------------------------------------------

@dataclass
class QuantityItem:
    """一行工程量"""
    item_name: str           # 项目名
    unit: str                # 单位
    qty: float               # 工程量
    price: float             # 综合单价(含税)
    specialty: Optional[str] = None
    remark: Optional[str] = None


@dataclass
class CompositionResult:
    """一行组价结果"""
    item: QuantityItem
    total: float             # 合价 = qty * price
    breakdown: Dict[str, float] = field(default_factory=dict)


@dataclass
class QuoteResult:
    """完整报价结果"""
    stage: str               # 估算/概算/预算/结算
    region: str              # 地区
    tax_method: str          # 一般计税 / 简易计税
    items: List[CompositionResult]  # 一类(分部分项)明细
    category1: float = 0.0   # 一类合计(分部分项)
    category2: float = 0.0   # 二类合计(措施费)
    category3: float = 0.0   # 三类合计(规费+税金)
    category2_detail: Dict[str, float] = field(default_factory=dict)  # 二类细分
    category3_detail: Dict[str, float] = field(default_factory=dict)  # 三类细分
    grand_total: float = 0.0  # 工程总造价 = 一类 + 二类 + 三类


# ---------------------------------------------------------------------------
# 默认费率(被 t_fee_rate 表覆盖)
# ---------------------------------------------------------------------------

DEFAULT_FEE_RATES = {
    "安全文明施工": 0.035,    # 3.5%
    "夜间施工": 0.005,       # 0.5%
    "二次搬运": 0.005,        # 0.5%
    "冬雨季施工": 0.005,      # 0.5%
    "已完工程保护": 0.005,    # 0.5%
    "规费": 0.25,            # 25%(社保+公积金+排污,以分部分项+措施+其他为基数)
}

# 一般计税 9% / 简易计税 3%
TAX_RATE_GENERAL = 0.09
TAX_RATE_SIMPLE = 0.03


# ---------------------------------------------------------------------------
# 核心算法
# ---------------------------------------------------------------------------

def _round2(x: float) -> float:
    """2 位小数四舍五入"""
    return float(Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def compose_unit_price(
    material: float = 0.0,
    labor: float = 0.0,
    machine: float = 0.0,
    management_rate: float = 0.05,
    profit_rate: float = 0.05,
    fee_rate: float = 0.25,
    tax_rate: float = TAX_RATE_GENERAL,
) -> Dict[str, float]:
    """
    八项组价算法 - 综合单价(含税)

    材料 + 人工 + 机械 → 直接费
    管理费 = 直接费 × 管理费率
    利润 = (直接费 + 管理费) × 利润率
    规费 = (直接费 + 管理费 + 利润) × 规费率
    税金 = (直接费 + 管理费 + 利润 + 规费) × 税率
    综合单价 = 上面五项之和
    """
    direct = material + labor + machine
    management = direct * management_rate
    profit = (direct + management) * profit_rate
    fee = (direct + management + profit) * fee_rate
    tax = (direct + management + profit + fee) * tax_rate
    unit_price = direct + management + profit + fee + tax
    return {
        "材料费": _round2(material),
        "人工费": _round2(labor),
        "机械费": _round2(machine),
        "直接费": _round2(direct),
        "管理费": _round2(management),
        "利润": _round2(profit),
        "规费": _round2(fee),
        "税金": _round2(tax),
        "综合单价(含税)": _round2(unit_price),
    }


def compose_quote(
    items: List[QuantityItem],
    region: str = "全国",
    stage: str = "预算",
    tax_method: str = "一般计税",
    fee_rates: Optional[Dict[str, float]] = None,
) -> QuoteResult:
    """
    完整报价组价算法

    输入:
      items:         工程量条目(每条含已查到的综合单价)
      region:        地区
      stage:         阶段(估算/概算/预算/结算)
      tax_method:    一般计税 / 简易计税
      fee_rates:     各二类三类费率,如未提供用 DEFAULT_FEE_RATES

    输出:
      QuoteResult: 含一/二/三类费用及总造价
    """
    rates = {**DEFAULT_FEE_RATES, **(fee_rates or {})}
    tax_rate = TAX_RATE_GENERAL if tax_method == "一般计税" else TAX_RATE_SIMPLE

    # ---- 一类(分部分项)----
    comp_items = []
    cat1 = 0.0
    for it in items:
        total = _round2(it.qty * it.price)
        comp = CompositionResult(item=it, total=total, breakdown={
            "工程量": it.qty,
            "综合单价": it.price,
            "合价": total,
        })
        comp_items.append(comp)
        cat1 += total
    cat1 = _round2(cat1)

    # ---- 二类(措施费)----
    cat2_detail = {}
    cat2 = 0.0
    # 各项措施费以"分部分项合计"为基数
    for fee_name, rate in rates.items():
        if fee_name == "规费":
            continue
        amount = _round2(cat1 * rate)
        cat2_detail[fee_name] = amount
        cat2 += amount
    cat2 = _round2(cat2)

    # ---- 三类(规费 + 税金)----
    cat3_detail = {}
    fee_amount = _round2((cat1 + cat2) * rates["规费"])
    cat3_detail["规费"] = fee_amount
    # 税金以"分部分项 + 措施 + 规费"为基数
    tax_amount = _round2((cat1 + cat2 + fee_amount) * tax_rate)
    cat3_detail[f"税金({tax_method}, {_round2(tax_rate*100)}%)"] = tax_amount
    cat3 = _round2(fee_amount + tax_amount)

    grand = _round2(cat1 + cat2 + cat3)

    return QuoteResult(
        stage=stage, region=region, tax_method=tax_method,
        items=comp_items,
        category1=cat1, category2=cat2, category3=cat3,
        category2_detail=cat2_detail,
        category3_detail=cat3_detail,
        grand_total=grand,
    )


# ---------------------------------------------------------------------------
# 单元测试
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("报价组价算法 - 自测")
    print("=" * 60)

    # 测试 1: 单价组价
    print("\n[1] 八项组价测试(材料100+人工50+机械30)")
    r = compose_unit_price(material=100, labor=50, machine=30)
    for k, v in r.items():
        print(f"  {k:18s}: {v}")

    # 测试 2: 完整报价
    print("\n[2] 完整报价(3 行工程量,北京,预算,一般计税)")
    items = [
        QuantityItem(item_name="C30 商品混凝土", unit="m³", qty=100, price=540.32),
        QuantityItem(item_name="φ12 钢筋", unit="t", qty=5.5, price=5980.0),
        QuantityItem(item_name="模板安拆", unit="m²", qty=200, price=85.50),
    ]
    quote = compose_quote(items, region="北京市", stage="预算", tax_method="一般计税")
    print(f"  一类(分部分项): {quote.category1}")
    print(f"  二类(措施费): {quote.category2}")
    for k, v in quote.category2_detail.items():
        print(f"    - {k}: {v}")
    print(f"  三类(规费+税金): {quote.category3}")
    for k, v in quote.category3_detail.items():
        print(f"    - {k}: {v}")
    print(f"  工程总造价: {quote.grand_total}")
    print(f"  (一类+二类+三类 = {quote.category1+quote.category2+quote.category3})")
