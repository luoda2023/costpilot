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
    )
  except json.JSONDecodeError:
    raise HTTPException(422, f"AI 返回格式异常,无法解析: {raw[:200]}")
  except (AIConfigError, AIClientError) as e:
    raise HTTPException(503, f"AI 服务不可用: {e}")
  except Exception as e:
    raise HTTPException(500, f"解析失败: {e}")


@router.post("/import-excel")
async def import_excel(file: UploadFile = File(...)):
  """
  AI 读取上传的 Excel 文件,理解全部数据后返回结构化字段

  流程:
  1. 接收用户上传的 Excel/CSV 文件
  2. 用 openpyxl 完整读取全部行
  3. 将全部数据转为文本,发给 AI 理解列含义
  4. AI 映射到 item_name/specialty/unit/qty/price 字段
  5. 返回结构化 JSON 数组
  """
  ALLOWED_EXTENSIONS = ('.xlsx', '.xls', '.csv')
  filename = file.filename or 'file.xlsx'
  ext = '.' + filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
  if ext not in ALLOWED_EXTENSIONS:
    raise HTTPException(400, f"不支持的文件格式: {ext}，请上传 .xlsx / .xls / .csv 文件")

  try:
    raw = await file.read()
  except Exception as e:
    raise HTTPException(400, f"文件读取失败: {e}")

  # --- 用 openpyxl 完整读取 Excel ---
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
    raise HTTPException(422, f"Excel 解析失败: {e}")

  if len(table_rows) < 2:
    raise HTTPException(400, "文件内容不足，需要至少包含表头和一行数据")

  # --- 转文本给 AI ---
  headers = table_rows[0]
  data_rows = table_rows[1:]

  # 限制行数防止 AI 超长(最多 200 行)
  MAX_ROWS = 200
  if len(data_rows) > MAX_ROWS:
    data_rows = data_rows[:MAX_ROWS]

  table_text = "表头: " + "\t".join(headers) + "\n"
  for i, row in enumerate(data_rows, 1):
    table_text += f"第{i}行: " + "\t".join(row) + "\n"

  system_prompt = """你是一个造价工程师,负责解析Excel表格数据。
表格列名可能不标准(如"项目名称/材料名称/名称/清单项目"→item_name)。

请理解表格的每一列含义,将每行数据映射到以下目标字段:
- item_name: 项目/材料名称(必填)
- specialty: 专业分类(土建/市政/安装/装饰/园林/钢结构/门窗幕墙/涂料等,根据名称判断)
- unit: 单位(如 m³/m²/t/个/套/根/㎡/m)
- qty: 数量(数字,没有则填0)
- price: 综合单价(数字,没有则填0)

注意: 请仔细阅读每一列的表头和数据,准确判断哪一列对应哪个字段。
如果某列明显是"序号"、"编号"、"备注"等无关列,请忽略。

输出严格 JSON 格式,不要输出任何其他文字:
{"rows":[{"item_name":"...","specialty":"...","unit":"...","qty":0,"price":0}]}"""

  try:
    raw_ai = _call_ai(system_prompt, f"请解析以下Excel表格的全部数据:\n\n{table_text}")
data = json.loads(raw_ai)
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
    )
  except json.JSONDecodeError:
    raise HTTPException(422, f"AI 返回格式异常,无法解析: {raw_ai[:200]}")
  except (AIConfigError, AIClientError) as e:
    raise HTTPException(503, f"AI 服务不可用: {e}")
  except Exception as e:
    raise HTTPException(500, f"解析失败: {e}")

def openpyxl_load_workbook(raw_bytes):
  """加载 Excel 工作簿(兼容 xlsx 和 xls)"""
  import openpyxl
  buf = io.BytesIO(raw_bytes)
  return openpyxl.load_workbook(buf, data_only=True)

@router.post("/fill-fields", response_model=FillFieldsOut)
def fill_fields(payload: FillFieldsIn):
  """
  AI 根据用户描述自动填充模板字段

  例如:
  字段: [{field_key:"building_name", field_label:"建筑名称"}, {field_key:"area", field_label:"建筑面积"}]
  描述: "某高层住宅1#楼,建筑面积12000㎡"
  → {"building_name": "某高层住宅1#楼", "area": "12000"}
  """
  if not payload.description.strip():
    raise HTTPException(400, "描述内容为空")

  fields_info = "\n".join([
    f"- {f['field_key']}: {f['field_label']}({'必填' if f.get('required') else '可选'}, 类型: {f.get('field_type', 'text')})"
    for f in payload.fields
  ])

  system_prompt = f"""你是一个造价工程师,根据用户描述自动填充模板字段。

目标字段:
{fields_info}

请从用户描述中提取对应字段的值。如果描述中没有相关信息,填入合理的默认值或空字符串。

输出严格 JSON 格式:
{{"field_key1": "值1", "field_key2": "值2"}}

不要输出任何其他文字。"""

  try:
raw = _call_ai(system_prompt, f"用户描述: {payload.description}")
 data = json.loads(raw)
 # 全角→半角清洗
 data = {k: to_half_width(v) if isinstance(v, str) else v for k, v in data.items()}
 return FillFieldsOut(values=data)
  except json.JSONDecodeError:
    raise HTTPException(422, f"AI 返回格式异常: {raw[:200]}")
  except (AIConfigError, AIClientError) as e:
    raise HTTPException(503, f"AI 服务不可用: {e}")
  except Exception as e:
    raise HTTPException(500, f"填充失败: {e}")


@router.post("/parse-project", response_model=ParseProjectOut)
def parse_project(payload: ParseProjectIn):
  """
  AI 根据用户一句话描述提取项目信息

  如: "帮我建一个北京某高层住宅的估算项目"
  → {"name": "北京某高层住宅估算", "region": "北京市", "stage": "估算"}
  """
  if not payload.description.strip():
    raise HTTPException(400, "描述内容为空")

  system_prompt = """你是一个造价工程师,从用户描述中提取项目信息。

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
 for key in ('name', 'region', 'stage', 'note'):
  if key in data and isinstance(data[key], str):
   data[key] = to_half_width(data[key])
 return ParseProjectOut(
  name=data.get("name", "")[:30],
  region=data.get("region", "全国"),
  stage=data.get("stage", "估算"),
  note=data.get("note", ""),
 )
  except json.JSONDecodeError:
    raise HTTPException(422, f"AI 返回格式异常: {raw[:200]}")
  except (AIConfigError, AIClientError) as e:
    raise HTTPException(503, f"AI 服务不可用: {e}")
  except Exception as e:
    raise HTTPException(500, f"解析失败: {e}")