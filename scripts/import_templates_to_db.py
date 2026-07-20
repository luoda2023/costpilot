r"""
造价通 - 8 类文本格式谱入库
从 H:\AI-model\文本编制模板库\ 下的 8 个格式谱 .md
拆为:
  - YAML 章节骨架(从 ## 与 ### 推断)
  - JSON 字段字典(从 ___、{{...}} 占位 + 必含项提取)
入库 t_template_type / t_template / t_template_field
"""
import re
import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from packages.server.db.database import SessionLocal, init_db
from packages.server.db.models import TemplateType, Template, TemplateField

# 8 类格式谱
TEMPLATE_TYPES = [
    (1, "可研报告", "report", "项目可行性研究报告"),
    (2, "施工组织设计", "manual", "总体/专题施工组织设计"),
    (3, "专项施工方案", "scheme", "单项工程施工方案"),
    (4, "技术交底与工艺标准", "manual", "工艺标准/作业指导书"),
    (5, "合同范本", "contract", "总包/分包/采购/劳务/勘察"),
    (6, "预结算与结算审计", "report", "结算书/审计方案/索赔"),
    (7, "造价分析手册与PPT培训", "manual", "定额分析/案例汇编/PPT 课件"),
    (8, "目标成本与概算", "report", "投资估算/目标成本/设计概算"),
]

# 各格式谱文件名
FORMATION_FILES = {
    1: "01_格式谱_可研报告.md",
    2: "02_格式谱_施工组织设计.md",
    3: "03_格式谱_专项施工方案.md",
    4: "04_格式谱_技术交底与工艺标准.md",
    5: "05_格式谱_合同范本.md",
    6: "06_格式谱_预结算与结算审计.md",
    7: "07_格式谱_造价分析手册与PPT培训.md",
    8: "08_格式谱_目标成本与概算.md",
}


def extract_skeleton_yaml(md_text: str, type_name: str) -> str:
    """从 markdown 中提取 ## 与 ### 章节骨架,生成 YAML"""
    lines = md_text.split("\n")
    chapters = []  # [(level, title)]
    for line in lines:
        m2 = re.match(r"^## (.+?)$", line)
        m3 = re.match(r"^### (.+?)$", line)
        if m3:
            chapters.append((3, m3.group(1).strip()))
        elif m2:
            chapters.append((2, m2.group(1).strip()))

    yaml_lines = [
        f"# {type_name} 章节骨架",
        f"doc_type: {type_name}",
        "chapters:",
    ]
    current_chapter = None
    for level, title in chapters:
        # 跳过"四、写作自检清单"等内容,但保留骨架
        if level == 2:
            yaml_lines.append(f"  - chapter: \"{title}\"")
            yaml_lines.append("    sections:")
            current_chapter = title
        elif level == 3 and current_chapter:
            yaml_lines.append(f"      - \"{title}\"")
    return "\n".join(yaml_lines)


def extract_fields(md_text: str) -> list:
    """
    提取字段定义:
    - 模板中的 {{field_key}} 占位
    - 表格列名 / 必含字段
    - 通用字段: project_name/region/stage/builder/invest/...
    """
    fields = []
    seen_keys = set()

    # 1) 通用必填字段(所有格式谱都有)
    common = [
        ("project_name", "项目名称", "text", True, None, None),
        ("region", "项目所在地", "select", True, None,
         ["北京市","上海市","天津市","重庆市","广东省","浙江省","江苏省","四川省","山东省","湖北省","湖南省","福建省","河北省","山西省","辽宁省","安徽省","江西省","河南省","海南省","贵州省","云南省","陕西省","甘肃省","青海省","内蒙古","广西","宁夏","新疆","西藏"]),
        ("stage", "工程阶段", "select", True, "估算", ["估算","概算","预算","结算"]),
        ("compiled_by", "编制人", "text", False, None, None),
        ("compiled_at", "编制日期", "date", False, None, None),
        ("reviewed_by", "审核人", "text", False, None, None),
        ("approved_by", "审批人", "text", False, None, None),
    ]
    for key, label, ftype, required, default, options in common:
        if key not in seen_keys:
            fields.append({"field_key": key, "field_label": label, "field_type": ftype,
                            "required": required, "default_value": default, "options": options})
            seen_keys.add(key)

    # 2) 提取 {{...}} 占位
    placeholders = re.findall(r"\{\{\s*([a-zA-Z_\u4e00-\u9fa5]+)\s*\}\}", md_text)
    for ph in placeholders:
        if ph not in seen_keys:
            fields.append({"field_key": ph, "field_label": ph, "field_type": "text",
                            "required": False, "default_value": "", "options": None})
            seen_keys.add(ph)

    # 3) 提取 ___ 下划线占位
    underscore_phs = re.findall(r"___+|______+", md_text)
    if underscore_phs:
        # 不计入具体字段,只标记
        pass

    # 4) 根据格式谱类型加特定字段(从表格中的"必含字段"提示)
    type_specific = {
        1: [  # 可研报告
            ("builder", "建设单位", "text", True, None, None),
            ("designer", "设计单位", "text", False, None, None),
            ("site_area", "用地面积(m²)", "number", False, None, None),
            ("building_area", "建筑面积(m²)", "number", True, None, None),
            ("total_invest", "总投资(万元)", "number", True, None, None),
            ("construction_period", "建设周期(月)", "number", False, None, None),
            ("irr", "内部收益率(%)", "number", False, None, None),
            ("npv", "净现值(万元)", "number", False, None, None),
            ("payback", "投资回收期(年)", "number", False, None, None),
        ],
        2: [  # 施工组织设计
            ("duration", "总工期(天)", "number", True, None, None),
            ("quality_target", "质量目标", "select", False, "合格", ["合格","优良","鲁班奖"]),
            ("safety_target", "安全目标", "text", False, "零事故", None),
            ("major_methods", "主要施工方法", "richtext", True, None, None),
        ],
        3: [  # 专项施工方案
            ("scheme_name", "方案名称", "text", True, None, None),
            ("risk_level", "危险等级", "select", False, "一般", ["一般","较大","重大"]),
            ("calc_required", "是否含计算书", "select", False, "否", ["是","否"]),
        ],
        4: [  # 技术交底
            ("process_name", "工艺名称", "text", True, None, None),
            ("applicable_scope", "适用范围", "text", True, None, None),
            ("crew", "作业班组", "text", False, None, None),
        ],
        5: [  # 合同
            ("party_a", "甲方", "text", True, None, None),
            ("party_b", "乙方", "text", True, None, None),
            ("contract_amount", "合同金额(元)", "number", False, None, None),
            ("contract_no", "合同编号", "text", False, None, None),
            ("sign_date", "签订日期", "date", False, None, None),
        ],
        6: [  # 预结算
            ("settlement_amount", "结算金额(元)", "number", True, None, None),
            ("audit_amount", "审减金额(元)", "number", False, None, None),
            ("claim_amount", "索赔金额(元)", "number", False, None, None),
        ],
        7: [  # 造价分析/PPT
            ("course_title", "课程名称", "text", False, None, None),
            ("audience", "授课对象", "text", False, None, None),
            ("duration_hours", "课时(小时)", "number", False, None, None),
        ],
        8: [  # 目标成本/概算
            ("cost_per_m2", "平米指标(元/m²)", "number", True, None, None),
            ("land_cost", "土地成本(万元)", "number", False, None, None),
            ("construction_cost", "建安成本(万元)", "number", True, None, None),
            ("equipment_cost", "设备成本(万元)", "number", False, None, None),
            ("other_cost", "其他费用(万元)", "number", False, None, None),
            ("reserve", "预备费(万元)", "number", False, None, None),
        ],
    }

    for key, label, ftype, required, default, options in type_specific.get(0, []):
        pass  # 不会执行
    for type_id, type_fields in type_specific.items():
        # 在使用时按 type_id 调用(下面 main 里)
        pass

    return fields, type_specific


def make_template_md(type_id: int, type_name: str, original_md: str) -> str:
    """生成可渲染的模板 markdown(简化版:在原 md 顶部插入字段占位区)"""
    header = f"""# {{project_name}} - {type_name}

> 编制地区: {{{{region}}}}  |  阶段: {{{{stage}}}}  |  编制人: {{{{compiled_by}}}}  |  日期: {{{{compiled_at}}}}

---
"""
    return header + original_md


def main():
    print("=" * 60)
    print("造价通 - 8 类文本格式谱入库")
    print("=" * 60)

    print("\n[1/3] 初始化数据库...")
    init_db()
    print("  [OK] 表结构就绪")

    print("\n[2/3] 写入 8 个格式谱类型...")
    session = SessionLocal()
    try:
        for tid, name, doc_type, desc in TEMPLATE_TYPES:
            tt = session.query(TemplateType).filter_by(id=tid).first()
            if not tt:
                tt = TemplateType(id=tid, name=name, doc_type=doc_type, description=desc)
                session.add(tt)
            else:
                tt.name = name
                tt.doc_type = doc_type
                tt.description = desc
        session.commit()
        print(f"  [OK] {len(TEMPLATE_TYPES)} 个类型已就位")

        print("\n[3/3] 解析并入库 8 个格式谱...")
        for tid, name, _, _ in TEMPLATE_TYPES:
            md_path = PROJECT_ROOT.parent / "文本编制模板库" / FORMATION_FILES[tid]
            if not md_path.exists():
                print(f"  [WARN] 文件不存在: {md_path}")
                continue

            md_text = md_path.read_text(encoding="utf-8")
            yaml_skeleton = extract_skeleton_yaml(md_text, name)
            fields, type_specific = extract_fields(md_text)
            # 追加类型特定字段
            for key, label, ftype, required, default, options in type_specific.get(tid, []):
                if not any(f["field_key"] == key for f in fields):
                    fields.append({"field_key": key, "field_label": label, "field_type": ftype,
                                   "required": required, "default_value": default, "options": options})

            template_md = make_template_md(tid, name, md_text)

            # 创建/更新模板记录
            t = session.query(Template).filter_by(type_id=tid, name=name).first()
            if not t:
                t = Template(type_id=tid, name=name, content_md=template_md, yaml_skeleton=yaml_skeleton,
                             version="1.0", is_active=True)
                session.add(t)
            else:
                t.content_md = template_md
                t.yaml_skeleton = yaml_skeleton
                t.version = "1.0"
                t.is_active = True
            session.commit()
            session.refresh(t)

            # 入库字段
            session.query(TemplateField).filter_by(template_id=t.id).delete()
            session.commit()
            for f in fields:
                tf = TemplateField(
                    template_id=t.id, field_key=f["field_key"], field_label=f["field_label"],
                    field_type=f["field_type"], required=f["required"],
                    default_value=f["default_value"], options=f["options"],
                )
                session.add(tf)
            session.commit()
            print(f"  [OK] {name}: 模板 + {len(fields)} 个字段已入库")

    finally:
        session.close()

    print("\n" + "=" * 60)
    print("8 类格式谱入库完毕")
    print("=" * 60)


if __name__ == "__main__":
    main()
