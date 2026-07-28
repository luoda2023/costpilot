"""根据官方标准更新DocGen大纲"""
import py_compile

with open('packages/server/api/ai_assist.py', 'r', encoding='utf-8') as f:
    content = f.read()

start = content.find('DOC_OUTLINES = {')
end = content.find('_DOC_TYPE_ALIAS = {')

new_outlines = '''DOC_OUTLINES = {
    # ==================== 可研报告(发改投资规〔2023〕304号) ====================
    "feas": {
        "feasibility": [
            ("一、项目概述", "overview", 600),
            ("二、项目建设背景和必要性", "necessity", 800),
            ("三、项目需求分析与产出方案", "demand", 800),
            ("四、项目选址与要素保障", "site", 600),
            ("五、项目建设方案", "scheme", 1200),
            ("六、项目运营方案", "operation", 600),
            ("七、项目投融资与财务方案", "finance", 1000),
            ("八、项目影响效果分析", "impact", 800),
            ("九、项目风险管控方案", "risk", 600),
            ("十、研究结论及建议", "conclusion", 500),
        ],
        "preliminary": [
            ("一、工程概况", "overview", 600),
            ("二、设计依据与范围", "design_basis", 500),
            ("三、建设规模与内容", "scale", 600),
            ("四、设计方案比选", "scheme_compare", 1000),
            ("五、推荐方案详细说明", "scheme_detail", 1200),
            ("六、主要工程量", "quantities", 600),
            ("七、投资估算", "estimate", 800),
            ("八、经济评价", "benefit", 600),
        ],
        "default": [
            ("一、项目概述", "overview", 600),
            ("二、建设内容与规模", "scale", 600),
            ("三、技术方案", "scheme", 800),
            ("四、投资估算", "estimate", 600),
            ("五、结论与建议", "conclusion", 400),
        ],
    },
    # ==================== 投标文件(深圳市招标范本2024) ====================
    "bid": {
        "feasibility": [
            ("一、项目管理机构与人员配置", "management", 600),
            ("二、施工管理重点难点分析及应对措施", "difficulty", 800),
            ("三、施工总体部署与总平面布置", "deployment", 800),
            ("四、施工进度计划及保证措施", "schedule", 800),
            ("五、主要分部分项工程施工技术方案", "construction_scheme", 1500),
            ("六、危大工程清单及安全管理措施", "dangerous", 800),
            ("七、施工机械设备配置计划", "equipment", 600),
            ("八、劳动力安排计划", "labor", 500),
            ("九、质量安全文明施工保证措施", "quality_safety", 800),
            ("十、绿色施工与环境保护措施", "environment", 600),
        ],
        "preliminary": [
            ("一、项目管理机构", "management", 500),
            ("二、施工重点难点分析", "difficulty", 600),
            ("三、施工总体部署", "deployment", 600),
            ("四、施工进度计划", "schedule", 600),
            ("五、主要施工技术方案", "construction_scheme", 1200),
            ("六、质量安全保证措施", "quality_safety", 600),
            ("七、资源配备计划", "resources", 500),
            ("八、各项管理保证措施", "management_measures", 600),
        ],
        "construction": [
            ("一、编制说明", "compile_note", 400),
            ("二、工程概况", "overview", 500),
            ("三、施工部署", "deployment", 600),
            ("四、施工进度计划", "schedule", 500),
            ("五、施工方案与技术措施", "construction_scheme", 1200),
            ("六、质量保证措施", "quality", 600),
            ("七、安全管理措施", "safety", 600),
            ("八、工期保证措施", "time_guarantee", 400),
        ],
        "default": [
            ("一、编制说明", "compile_note", 400),
            ("二、工程概况", "overview", 500),
            ("三、施工方案", "construction_scheme", 1000),
            ("四、质量安全措施", "quality_safety", 600),
            ("五、进度计划", "schedule", 400),
        ],
    },
    # ==================== 初步设计说明(住建部深度规定2016版第3章) ====================
    "prelim": {
        "feasibility": [
            ("一、设计说明书", "design_desc", 800),
            ("二、工程概况", "overview", 600),
            ("三、设计依据与主要规范", "standards", 500),
            ("四、建设规模与设计范围", "scale", 600),
            ("五、总平面设计", "general_layout", 800),
            ("六、建筑专业设计说明", "architecture", 1000),
            ("七、结构专业设计说明", "structure", 1000),
            ("八、给排水专业设计说明", "plumbing", 800),
            ("九、电气专业设计说明", "electrical", 800),
            ("十、暖通专业设计说明", "hvac", 600),
            ("十一、主要技术经济指标", "economic", 600),
            ("十二、概算书", "estimate", 800),
        ],
        "preliminary": [
            ("一、设计说明书", "design_desc", 800),
            ("二、工程概况", "overview", 600),
            ("三、设计依据与规范", "standards", 500),
            ("四、建设规模", "scale", 500),
            ("五、总平面设计", "general_layout", 800),
            ("六、各专业设计方案", "design_detail", 1500),
            ("七、主要工程数量", "quantities", 600),
            ("八、施工组织建议", "construction_org", 500),
            ("九、概算书", "estimate", 800),
        ],
        "construction": [
            ("一、设计说明书", "design_desc", 600),
            ("二、工程概况", "overview", 500),
            ("三、设计依据", "standards", 400),
            ("四、设计范围与内容", "scale", 500),
            ("五、各专业设计方案", "design_detail", 1200),
            ("六、主要工程量", "quantities", 500),
            ("七、概算", "estimate", 600),
        ],
        "default": [
            ("一、设计说明书", "design_desc", 600),
            ("二、工程概况", "overview", 500),
            ("三、设计方案", "design_detail", 1000),
            ("四、主要工程量", "quantities", 400),
            ("五、概算", "estimate", 500),
        ],
    },
    # ==================== 施工图设计说明(住建部深度规定2016版第4章) ====================
    "draw": {
        "feasibility": [
            ("一、设计说明书", "design_desc", 600),
            ("二、工程概况", "overview", 500),
            ("三、设计依据与规范", "standards", 400),
            ("四、建筑专业设计说明", "architecture", 1000),
            ("五、结构专业设计说明", "structure", 1000),
            ("六、给排水专业设计说明", "plumbing", 800),
            ("七、电气专业设计说明", "electrical", 800),
            ("八、施工注意事项", "construction_req", 800),
            ("九、材料与设备表", "materials", 600),
        ],
        "preliminary": [
            ("一、设计说明书", "design_desc", 600),
            ("二、工程概况", "overview", 500),
            ("三、设计依据", "standards", 400),
            ("四、建筑专业设计", "architecture", 1000),
            ("五、结构专业设计", "structure", 1000),
            ("六、给排水专业设计", "plumbing", 800),
            ("七、电气专业设计", "electrical", 800),
            ("八、施工要求", "construction_req", 600),
            ("九、材料设备清单", "materials", 500),
        ],
        "construction": [
            ("一、设计说明书", "design_desc", 500),
            ("二、工程概况", "overview", 400),
            ("三、设计依据", "standards", 400),
            ("四、各专业设计说明", "design_detail", 1200),
            ("五、施工要求", "construction_req", 800),
            ("六、质量验收标准", "quality", 600),
            ("七、材料设备表", "materials", 500),
        ],
        "default": [
            ("一、设计说明", "design_desc", 500),
            ("二、工程概况", "overview", 400),
            ("三、各专业设计说明", "design_detail", 1000),
            ("四、施工要求", "construction_req", 600),
            ("五、材料设备表", "materials", 400),
        ],
    },
    # ==================== 施工组织设计(GB/T 50502-2009) ====================
    "constr": {
        "feasibility": [
            ("一、编制依据", "basis", 400),
            ("二、工程概况", "overview", 600),
            ("三、施工总体部署", "deployment", 800),
            ("四、施工总进度计划", "schedule", 600),
            ("五、施工总平面布置", "layout", 600),
            ("六、主要施工方法", "construction_scheme", 1500),
            ("七、施工准备与资源配置计划", "resources", 600),
            ("八、质量管理体系与措施", "quality", 800),
            ("九、安全管理体系与措施", "safety", 800),
            ("十、环境管理计划", "environment", 600),
            ("十一、成本管理计划", "cost", 500),
            ("十二、进度管理计划", "schedule_manager", 500),
            ("十三、其他管理计划", "other", 400),
        ],
        "preliminary": [
            ("一、编制依据", "basis", 400),
            ("二、工程概况", "overview", 600),
            ("三、施工部署", "deployment", 600),
            ("四、施工进度计划", "schedule", 600),
            ("五、施工平面布置", "layout", 500),
            ("六、主要施工方案", "construction_scheme", 1200),
            ("七、质量保证措施", "quality", 600),
            ("八、安全保障措施", "safety", 600),
            ("九、资源配置", "resources", 400),
        ],
        "construction": [
            ("一、编制依据", "basis", 300),
            ("二、工程概况", "overview", 500),
            ("三、施工部署", "deployment", 600),
            ("四、施工进度计划", "schedule", 500),
            ("五、施工方案", "construction_scheme", 1200),
            ("六、质量安全措施", "quality_safety", 600),
            ("七、环境保护措施", "environment", 400),
        ],
        "default": [
            ("一、编制依据", "basis", 300),
            ("二、工程概况", "overview", 500),
            ("三、施工部署与方案", "construction_scheme", 1000),
            ("四、质量安全保障", "quality_safety", 600),
            ("五、进度与资源配置", "schedule_resources", 400),
        ],
    },
    # ==================== 方案说明/比选方案 ====================
    "proposal": {
        "feasibility": [
            ("一、方案概述", "intro", 400),
            ("二、现状分析与问题诊断", "status", 600),
            ("三、方案比选", "compare", 1000),
            ("四、推荐方案详细说明", "scheme_detail", 1200),
            ("五、预期效果分析", "effect", 600),
            ("六、投资估算", "estimate", 600),
            ("七、实施计划", "implementation", 400),
        ],
        "preliminary": [
            ("一、方案概述", "intro", 400),
            ("二、现状分析", "status", 500),
            ("三、方案比选", "compare", 800),
            ("四、推荐方案", "scheme_detail", 1000),
            ("五、投资估算", "estimate", 500),
            ("六、实施建议", "implementation", 400),
        ],
        "construction": [
            ("一、方案概述", "intro", 300),
            ("二、方案说明", "scheme_detail", 1000),
            ("三、投资估算", "estimate", 500),
            ("四、实施计划", "implementation", 400),
        ],
        "default": [
            ("一、方案概述", "intro", 300),
            ("二、方案说明", "scheme_detail", 800),
            ("三、投资估算", "estimate", 400),
        ],
    },
    # ==================== 概算/目标成本(GB/T 51095) ====================
    "cost": {
        "feasibility": [
            ("一、编制说明", "compile_note", 400),
            ("二、编制依据", "basis", 400),
            ("三、工程概况", "overview", 400),
            ("四、投资估算汇总表", "estimate_table", 600),
            ("五、各专业造价分析", "cost_analysis", 800),
            ("六、单方造价指标", "unit_cost", 400),
            ("七、投资合理性分析", "reasonability", 400),
        ],
        "preliminary": [
            ("一、编制说明", "compile_note", 400),
            ("二、编制依据", "basis", 400),
            ("三、工程概况", "overview", 400),
            ("四、概算书", "estimate_table", 600),
            ("五、各专业概算", "cost_analysis", 800),
            ("六、技术经济指标", "unit_cost", 400),
            ("七、概算对比分析", "comparison", 400),
        ],
        "construction": [
            ("一、编制说明", "compile_note", 300),
            ("二、编制依据", "basis", 300),
            ("三、工程概况", "overview", 300),
            ("四、预算书", "estimate_table", 600),
            ("五、各专业预算", "cost_analysis", 600),
            ("六、指标分析", "unit_cost", 400),
        ],
        "default": [
            ("一、编制说明", "compile_note", 300),
            ("二、编制依据", "basis", 300),
            ("三、造价汇总", "estimate_table", 500),
            ("四、造价分析", "cost_analysis", 500),
        ],
    },
    # ==================== 合同范本 ====================
    "contract": {
        "feasibility": [
            ("一、合同协议书", "agreement", 600),
            ("二、通用合同条款", "general_clauses", 1000),
            ("三、专用合同条款", "special_clauses", 1000),
            ("四、工程质量与验收", "quality", 600),
            ("五、合同价款与支付", "payment", 800),
            ("六、变更与索赔", "change", 600),
            ("七、违约责任", "penalty", 400),
            ("八、争议解决", "dispute", 400),
        ],
        "preliminary": [
            ("一、合同协议书", "agreement", 500),
            ("二、合同条款", "general_clauses", 800),
            ("三、专用条款", "special_clauses", 800),
            ("四、价款与支付", "payment", 600),
            ("五、质量与验收", "quality", 500),
            ("六、违约责任", "penalty", 400),
        ],
        "construction": [
            ("一、合同主要条款", "general_clauses", 800),
            ("二、工程范围与内容", "scope", 500),
            ("三、价款与支付", "payment", 600),
            ("四、质量与工期", "quality", 500),
            ("五、违约责任", "penalty", 400),
        ],
        "default": [
            ("一、合同主要条款", "general_clauses", 600),
            ("二、价款与支付", "payment", 500),
            ("三、质量与工期", "quality", 400),
            ("四、违约责任", "penalty", 300),
        ],
    },
}

_DOC_TYPE_ALIAS = {
    "bid": "bid",
    "proposal": "proposal",
    "prelim": "prelim",
    "draw": "draw",
    "feas": "feas",
    "constr": "constr",
    "contract": "contract",
    "cost": "cost",
}
'''

content = content[:start] + new_outlines + content[end:]
with open('packages/server/api/ai_assist.py', 'w', encoding='utf-8') as f:
    f.write(content)

py_compile.compile('packages/server/api/ai_assist.py', doraise=True)
print('Done! Syntax OK')