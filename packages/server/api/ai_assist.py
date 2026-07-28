"""
工程助手 - AI 智能辅助 API

提供 AI 驱动的智能导入/填充功能:
  POST /api/v1/ai/parse-table 理解任意格式表格数据,返回结构化字段
  POST /api/v1/ai/import-excel 上传 Excel 文件,AI 完整读取后填充
  POST /api/v1/ai/fill-fields 根据模板字段+用户描述,AI 自动填充字段值
  POST /api/v1/ai/parse-project 根据用户一句话描述,提取项目信息

设计原则:
  - 不要求用户上传固定格式文件
  - AI 理解内容后自动映射到系统字段
  - 所有接口返回结构化 JSON,前端直接填充
"""
import json
import io
import re
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from packages.server.ai.client import get_ai_client, AIClientError, AIConfigError
from packages.server.utils.format import to_half_width
from packages.server.utils.logger import logger

router = APIRouter()

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ParseTableIn(BaseModel):
  """表格解析请求"""
  content: str  # 文件文本内容(CSV/Excel 转 text/json)
  source_type: str = "auto"  # auto / csv / json / text
  target_fields: List[str] = ["item_name", "specialty", "unit", "qty", "price"]

class ParseTableOut(BaseModel):
  """表格解析响应"""
  rows: List[Dict[str, Any]]
  total: int
  parsed: int
  column_mapping: Dict[str, str] = {}  # {field_name: original_header_text}

class FillFieldsIn(BaseModel):
    """字段填充请求"""
    fields: List[Dict[str, Any]]  # [{field_key, field_label, field_type, required, default_value}]
    description: str  # 用户描述,如"某高层住宅1#楼,建筑面积12000㎡,框架结构"

class FillFieldsOut(BaseModel):
  """字段填充响应"""
  values: Dict[str, Any]  # {field_key: filled_value}, 支持字符串/数字/布尔值

class ParseProjectIn(BaseModel):
  description: str  # 如"帮我建一个北京某高层住宅的估算项目"

class ParseProjectOut(BaseModel):
 name: str
 region: str
 stage: str
 note: str = ""

class DocSectionIn(BaseModel):
 """单节文档生成请求"""
 section_title: str  # 节标题,如"一、总论"
 section_key: str  # 节标识,如"general"
 doc_type: str  # 文档类型: bid/proposal/prelim/draw/feas/constr/contract/cost
 stage: str  # 阶段: feasibility/preliminary/construction/building/settlement
 eng_type: str  # 工程类型: pipeline/road/building/water/landscape/mep/other
 project_info: Dict[str, Any]  # 项目信息
 word_count: int = 500  # 目标字数
 context: str = ""  # 前文内容(用于保持风格一致)

class DocSectionOut(BaseModel):
 """单节文档生成响应"""
 section_title: str
 section_key: str
 content: str  # Markdown 格式内容
 actual_words: int  # 实际生成字数

# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------

def _call_ai(system_prompt: str, user_prompt: str) -> str:
    """调用 AI 并返回响应文本,自动提取 JSON 块"""
    client = get_ai_client()
    resp = client.chat(messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ])
    content = resp.get("content", "")
    # 尝试提取 JSON 块(跳过 markdown 代码块标记)
    content = content.strip()
    # 先处理 markdown 代码块 ```json ... ```
    if content.startswith("```"):
        lines = content.split("\n")
        start = next((i for i, l in enumerate(lines) if "```" in l), -1)
        end = next((i for i in range(start + 1, len(lines)) if "```" in lines[i]), len(lines))
        if start >= 0:
            content = "\n".join(lines[start + 1:end]).strip()
    # 如果内容不是纯 JSON(有中文等),尝试用正则提取第一个 { ... } 或 [ ... ]
    if not (content.startswith("{") or content.startswith("[")):
        import re
        # 找 {...} 或 [...] 块
        for pattern in [r'(\{.*\})', r'(\[.*\])']:
            m = re.search(pattern, content, re.DOTALL)
            if m:
                content = m.group(1)
                break
    return content

# ---------------------------------------------------------------------------
# 路由
# ---------------------------------------------------------------------------

@router.post("/parse-table", response_model=ParseTableOut)
def parse_table(payload: ParseTableIn):
    """
    AI 理解任意格式表格数据,返回结构化字段

    流程:
    1. 接收用户上传的表格文本内容(CSV/Excel 转 text)
    2. AI 理解表格列含义,映射到目标字段
    3. 返回结构化 JSON 数组
    """
    if not payload.content.strip():
        raise HTTPException(400, "内容为空")

    system_prompt = """你是一个造价工程师,负责解析各种格式的表格数据。
表格可能来自 Excel、CSV 或文本格式,列名可能不标准(如"项目名称/材料名称/名称"→item_name)。

请理解表格的列含义,将每行数据映射到以下目标字段:
- item_name: 项目/材料名称(必填)
- specialty: 专业分类(土建/市政/安装/装饰/园林/钢结构/门窗幕墙/涂料等)
- unit: 单位(如 m³/m²/t/个/套/根/㎡/m)
- qty: 数量(数字,没有则填0)
- price: 综合单价(数字,没有则填0)

输出严格 JSON 格式:
{"rows":[{"item_name":"...","specialty":"...","unit":"...","qty":0,"price":0}]}

不要输出任何其他文字。"""

    try:
        raw = _call_ai(system_prompt, f"请解析以下表格数据:\n\n{payload.content[:10000]}")
        # 解析 JSON
        data = json.loads(raw)
        rows = data.get("rows", [])
        # 全角→半角清洗
        for row in rows:
            for key in ('item_name', 'specialty', 'unit', 'price', 'qty'):
                if key in row and isinstance(row[key], str):
                    row[key] = to_half_width(row[key])
        return ParseTableOut(
            rows=rows,
            total=len(rows),
            parsed=sum(1 for r in rows if r.get("item_name")),
            column_mapping={},
        )
    except json.JSONDecodeError:
        logger.warning("parse-table AI 返回非 JSON: %.200s", raw)
        raise HTTPException(422, "AI 返回格式异常，请重试")
    except (AIConfigError, AIClientError) as e:
        logger.error("parse-table AI 服务不可用: %s", e)
        raise HTTPException(503, "AI 服务暂不可用，请检查配置")
    except Exception as e:
        logger.error("parse-table 解析失败: %s", e, exc_info=True)
        raise HTTPException(500, "表格解析失败，请稍后重试")


@router.post("/import-excel")
async def import_excel(file: UploadFile = File(...)):
  """
  AI 读取上传的 Excel 文件,理解全部数据后返回结构化字段

  流程:
  1. 接收用户上传的 Excel/CSV 文件
  2. 用 openpyxl 完整读取全部行
  3. 本地规则解析表头列映射(优先，快速准确)
  4. 本地无法识别的列交给 AI 补充
  5. 返回结构化 JSON 数组
  """
  ALLOWED_EXTENSIONS = ('.xlsx', '.xls', '.csv')
  MAX_FILE_SIZE = 10 * 1024 * 1024
  filename = file.filename or 'file.xlsx'
  ext = '.' + filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
  if ext not in ALLOWED_EXTENSIONS:
    raise HTTPException(400, f"不支持的文件格式: {ext}，请上传 .xlsx / .xls / .csv 文件")

  try:
    raw = await file.read()
    if len(raw) > MAX_FILE_SIZE:
      raise HTTPException(413, "文件过大，请上传 10MB 以内的文件")
  except HTTPException:
    raise
  except Exception as e:
    logger.error("import-excel 文件读取失败: %s", e, exc_info=True)
    raise HTTPException(400, "文件读取失败，请检查文件是否损坏")

  # --- 读取表格 ---
  table_rows = []
  try:
    if ext == '.csv':
      import csv
      content = raw.decode('utf-8-sig', errors='replace')
      reader = csv.reader(io.StringIO(content))
      for row in reader:
        table_rows.append(row)
    else:
      wb = openpyxl_load_workbook(raw)
      ws = wb.active
      for row in ws.iter_rows(values_only=True):
        table_rows.append([str(v) if v is not None else '' for v in row])
  except Exception as e:
    logger.error("import-excel openpyxl 解析失败: %s", e, exc_info=True)
    raise HTTPException(422, "Excel 解析失败，请确保文件内容为有效表格格式")

  if len(table_rows) < 2:
    raise HTTPException(400, "文件内容不足，需要至少包含表头和一行数据")

  # --- Step 1: 本地规则解析表头列映射 ---
  headers = table_rows[0]
  data_rows = table_rows[1:]

  # 列名关键词映射表
  COLUMN_RULES = {
    'item_name': ['项目名称', '项目名', '材料名称', '材料名', '名称', '清单项目', '项目', '名称规格', '分部分项', '项目特征', '名称及规格', '构件名称', '部位名称'],
    'qty': ['工程量', '数量', '工程量(m)', '工程量(m2)', '工程量(m3)', '合计数量', '设计数量', '清单工程量', '实算工程量', '单位工程量'],
    'unit': ['单位', '计量单位', '单位(m3)', '单位(m2)', '单位(m)', '单位(t)', '单位(个)'],
    'price': ['单价', '综合单价', '预算单价', '信息价', '市场价', '参考价', '合价'],
    'specialty': ['专业', '专业类别', '工程类别', '专业分类', '分部工程'],
    'remark': ['备注', '说明', '注释', '描述'],
  }

  def _match_column(header: str) -> str | None:
    """根据列名匹配目标字段"""
    h = header.strip().lower()
    h_no_space = re.sub(r'[\s\-_/（(）)]', '', h)
    for field, keywords in COLUMN_RULES.items():
      for kw in keywords:
        kw_clean = re.sub(r'[\s\-_/（(）)]', '', kw.lower())
        if kw_clean in h or kw_clean in h_no_space or h_no_space in kw_clean:
          return field
    return None

  col_map = {}  # {field_name: col_index}
  for i, h in enumerate(headers):
    field = _match_column(h)
    if field:
      # 同一字段优先取第一个匹配
      if field not in col_map:
        col_map[field] = i

  logger.info("import-excel 列映射: %s", {k: f"{headers[v]}(列{v})" for k, v in col_map.items()})

  # --- Step 2: 本地解析数据行 ---
  rows = []
  for row_data in data_rows:
    if not any(v.strip() for v in row_data):
      continue  # 跳过空行
    r = {
      'item_name': '',
      'specialty': '',
      'unit': '',
      'qty': 0,
      'price': 0,
      'remark': '',
    }
    # 通过列映射填充
    for field, col_idx in col_map.items():
      if col_idx < len(row_data):
        val = row_data[col_idx].strip()
        if field in ('qty', 'price'):
          # 提取数字
          num_match = re.search(r'[\d,]+\.?\d*', val.replace(',', ''))
          r[field] = float(num_match.group()) if num_match else 0
        else:
          r[field] = to_half_width(val)

    # 全角→半角清洗
    for key in r:
      if isinstance(r[key], str):
        r[key] = to_half_width(r[key])

    rows.append(r)

  # --- Step 3: 如果本地解析不够好(缺少关键列)，用 AI 补充 ---
  parsed_count = sum(1 for r in rows if r.get('item_name'))
  # 判断是否需要 AI 补充: 没有 item_name 列 或 解析结果太少
  needs_ai = 'item_name' not in col_map or parsed_count < len(rows) * 0.5

  if needs_ai and rows:
    try:
      client = get_ai_client()
      # 构建简化表格文本（只发前50行避免超长）
      sample_rows = rows[:50]
      sample_text = "表头: " + "\t".join(headers) + "\n"
      for i, r in enumerate(sample_rows, 1):
        sample_text += f"第{i}行: {r.get('item_name','?')}\t{r.get('specialty','?')}\t{r.get('unit','?')}\t{r.get('qty',0)}\t{r.get('price',0)}\n"

      system_prompt = """你是一个造价工程师,正在补充解析Excel表格数据。
部分列已由本地规则识别，请你补全未能识别的列。

表格已有部分字段，如果某行 item_name 为空但表格中有项目名称，请填入。
请输出严格JSON: {"rows":[{"item_name":"...","specialty":"...","unit":"...","qty":0,"price":0}]}"""

      raw_ai = client.chat(messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"请补充以下表格中缺失的 item_name 和价格字段:\n\n{sample_text}\n\n已识别列: {list(col_map.keys())}"},
      ])
      ai_text = raw_ai.get("content", "")
      data = json.loads(ai_text)
      ai_rows = data.get("rows", [])
      # 合并 AI 结果：只补充空白字段
      for i, ai_row in enumerate(ai_rows):
        if i < len(rows):
          for key in ('item_name', 'specialty', 'unit', 'qty', 'price'):
            if key in ai_row and ai_row[key] and not rows[i].get(key):
              rows[i][key] = to_half_width(str(ai_row[key])) if isinstance(ai_row[key], str) else ai_row[key]
      parsed_count = sum(1 for r in rows if r.get('item_name'))
      logger.info("import-excel AI 补充后解析 %d/%d 行", parsed_count, len(rows))
    except (AIClientError, AIConfigError) as e:
      logger.warning("import-excel AI 补充失败(使用本地结果): %s", e)
    except Exception as e:
      logger.warning("import-excel AI 补充异常(使用本地结果): %s", e)

  # 过滤掉完全空白的行
  rows = [r for r in rows if r.get('item_name') or r.get('qty') or r.get('price')]

  # 限制行数
  if len(rows) > MAX_ROWS:
    rows = rows[:MAX_ROWS]

  return ParseTableOut(
    rows=rows,
    total=len(rows),
    parsed=sum(1 for r in rows if r.get('item_name')),
    # 返回列映射信息供前端展示
    column_mapping={k: headers[v] for k, v in col_map.items()},
  )


def openpyxl_load_workbook(raw_bytes):
  """加载 Excel 工作簿(兼容 xlsx 和 xls)"""
  import openpyxl
  buf = io.BytesIO(raw_bytes)
  return openpyxl.load_workbook(buf, data_only=True)

@router.post("/parse-project", response_model=ParseProjectOut)
def parse_project(payload: ParseProjectIn):
    """
    AI 根据用户一句话描述提取项目信息

    如: "帮我建一个北京某高层住宅的估算项目"
    → {"name": "北京某高层住宅估算", "region": "北京市", "stage": "估算"}
    """
    if not payload.description.strip():
        raise HTTPException(400, "描述内容为空")

    system_prompt = """你是一个造价工程师,从用户描述中提取项目信息.

输出严格 JSON 格式:
{
  "name": "项目名称(从描述中提取,长度不超过30字)",
  "region": "地区(必须是以下之一: 北京市/上海市/天津市/重庆市/广东省/浙江省/江苏省/四川省/山东省/湖北省/湖南省/福建省/河北省/河南省/安徽省/江西省,如果无法确定填'全国')",
  "stage": "项目阶段(估算/概算/预算/结算,如果无法确定填'估算')",
  "note": "备注(提取其他有用信息,如建筑面积、结构类型等)"
}

不要输出任何其他文字。"""

    try:
        raw = _call_ai(system_prompt, f"用户描述: {payload.description}")
        data = json.loads(raw)
        # 全角→半角清洗
        for key in ("name", "region", "stage", "note"):
            if key in data and isinstance(data[key], str):
                data[key] = to_half_width(data[key])
        return ParseProjectOut(
            name=data.get("name", "")[:30],
            region=data.get("region", "全国"),
            stage=data.get("stage", "估算"),
            note=data.get("note", ""),
        )
    except json.JSONDecodeError:
        logger.warning("parse-project AI 返回非 JSON: %.200s", raw)
        raise HTTPException(422, "AI 返回格式异常，请重试")
    except (AIConfigError, AIClientError) as e:
        logger.error("parse-project AI 服务不可用: %s", e)
        raise HTTPException(503, "AI 服务暂不可用，请检查配置")
    except Exception as e:
        logger.error("parse-project 解析失败: %s", e, exc_info=True)
        raise HTTPException(500, "项目解析失败，请稍后重试")

STAGE_NAME_MAP = {
    "feasibility": "可研/立项阶段",
    "preliminary": "初步设计/报批",
    "construction": "施工图/招投标",
    "building": "施工阶段",
    "settlement": "结算/审计",
}

ENG_TYPE_NAME_MAP = {
    "pipeline": "市政管网（给水/排水）",
    "road": "道路工程",
    "building": "建筑工程",
    "water": "水利工程",
    "landscape": "园林绿化",
    "mep": "机电安装",
    "other": "其他工程",
}

DOC_OUTLINES = {
    "bid": {
        "feasibility": [
            ("一、总论", "general", 800),
            ("二、建设必要性", "necessity", 600),
            ("三、建设规模与内容", "scale", 800),
            ("四、工程方案", "scheme", 1200),
            ("五、投资估算", "estimate", 1000),
            ("六、效益分析", "benefit", 600),
            ("七、结论与建议", "conclusion", 400),
        ],
        "preliminary": [
            ("一、设计说明", "design_desc", 1000),
            ("二、工程概况", "overview", 600),
            ("三、设计标准与依据", "standards", 800),
            ("四、工程设计方案", "design", 1500),
            ("五、主要工程数量", "quantities", 800),
            ("六、施工组织建议", "construction_org", 600),
        ],
        "construction": [
            ("一、设计说明", "design_desc", 1200),
            ("二、工程概况", "overview", 800),
            ("三、设计依据与标准", "standards", 600),
            ("四、主体工程设计", "main_design", 1500),
            ("五、附属设施设计", "auxiliary", 800),
            ("六、施工要求", "construction_req", 1000),
            ("七、质量验收标准", "quality", 600),
        ],
        "default": [
            ("一、总论", "general", 800),
            ("二、工程概况", "overview", 600),
            ("三、工程方案", "scheme", 1000),
            ("四、施工组织", "construction_org", 800),
            ("五、投资估算", "estimate", 800),
        ],
    },
}

_DOC_TYPE_ALIAS = {
    "proposal": "bid", "prelim": "bid", "draw": "bid", "feas": "bid",
    "constr": "bid", "contract": "bid", "cost": "bid",
}

def _resolve_outline(doc_type: str, stage: str) -> list:
    real_type = _DOC_TYPE_ALIAS.get(doc_type, doc_type)
    type_outlines = DOC_OUTLINES.get(real_type)
    if type_outlines is None:
        type_outlines = DOC_OUTLINES.get("bid", {})
    return type_outlines.get(stage, type_outlines.get("default", []))

def _build_section_prompt(section_title, section_key, doc_type, stage, eng_type, project_info, word_count, context) -> str:
    stage_name = STAGE_NAME_MAP.get(stage, stage)
    eng_name = ENG_TYPE_NAME_MAP.get(eng_type, eng_type)
    project_name = project_info.get("name", "本项目")
    location = project_info.get("location", "")
    scale = project_info.get("scale", "")
    scale_unit = project_info.get("scaleUnit", "")
    note = project_info.get("note", "")
    context_hint = ""
    if context:
        context_hint = "\n前文内容参考:\n" + context[:500] + "\n请保持与前文一致的写作风格和术语。\n"
    prompt = (
        "你是一位资深造价工程师和工程技术文档撰写专家。\n\n"
        "当前任务：撰写工程文档的单个章节。\n"
        "文档类型：" + doc_type + "\n"
        "编制阶段：" + stage_name + "\n"
        "工程类型：" + eng_name + "\n"
        "项目名称：" + project_name + "\n"
        "项目地点：" + location + "\n"
        "工程规模：" + scale + scale_unit + "\n"
        + ("补充说明：" + note + "\n" if note else "")
        + context_hint
        + "请撰写以下章节：\n【" + section_title + "】\n\n"
        "要求：\n"
        "1. 字数约 " + str(word_count) + " 字（不含标题）\n"
        "2. 内容专业、具体、符合" + stage_name + "的深度要求\n"
        "3. 结合" + eng_name + "类项目的技术特点和规范要求\n"
        "4. 数据合理、术语准确、逻辑清晰\n"
        "5. 使用 Markdown 格式输出（##/### 标题、- 列表、粗体等）\n\n"
        "只输出本章节内容，不要包含其他章节。"
    )
    return prompt


class DocOutlineOut(BaseModel):
    sections: List[Dict[str, Any]]
    doc_type: str
    stage: str
    eng_type: str

@router.get("/doc-gen/outline", response_model=DocOutlineOut)
def get_doc_outline(doc_type: str, stage: str, eng_type: str = "default"):
    outline = _resolve_outline(doc_type, stage)
    sections = [
        {"title": title, "key": key, "word_count": wc}
        for title, key, wc in outline
    ]
    return DocOutlineOut(
        sections=sections,
        doc_type=doc_type,
        stage=stage,
        eng_type=eng_type,
    )

@router.post("/doc-gen/section", response_model=DocSectionOut)
def generate_doc_section(payload: DocSectionIn):
    try:
        client = get_ai_client()
        prompt = _build_section_prompt(
            payload.section_title, payload.section_key,
            payload.doc_type, payload.stage, payload.eng_type,
            payload.project_info, payload.word_count, payload.context
        )
        resp = client.chat(messages=[
            {"role": "system", "content": "你是一位资深造价工程师，擅长撰写各类工程技术文档。请严格按照要求输出。"},
            {"role": "user", "content": prompt},
        ])
        content = resp.get("content", "")
        if content.startswith("```"):
            content = "\n".join(content.split("\n")[1:])
        if content.endswith("```"):
            content = "\n".join(content.split("\n")[:-1])
        actual_words = len(content.replace("\n", "").replace(" ", "").replace("|", ""))
        logger.info("doc-gen 节生成: %s, 字数=%d", payload.section_title, actual_words)
        return DocSectionOut(
            section_title=payload.section_title,
            section_key=payload.section_key,
            content=content.strip(),
            actual_words=actual_words,
        )
    except (AIClientError, AIConfigError) as e:
        logger.error("doc-gen 节生成失败: %s", e)
        raise HTTPException(503, "AI 服务暂不可用: " + str(e))
    except Exception as e:
        logger.error("doc-gen 节生成异常: %s", e, exc_info=True)
        raise HTTPException(500, "文档节生成失败，请稍后重试")
