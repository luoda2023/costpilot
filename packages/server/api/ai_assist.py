"""
造价通 - AI 智能辅助 API

提供 AI 驱动的智能导入/填充功能:
  POST /api/v1/ai/parse-table   理解任意格式表格数据,返回结构化字段
  POST /api/v1/ai/fill-fields   根据模板字段+用户描述,AI 自动填充字段值
  POST /api/v1/ai/parse-project 根据用户一句话描述,提取项目信息

设计原则:
  - 不要求用户上传固定格式文件
  - AI 理解内容后自动映射到系统字段
  - 所有接口返回结构化 JSON,前端直接填充
"""
import json
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from packages.server.ai.client import get_ai_client, AIClientError, AIConfigError

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
  fields: List[Dict[str, str]]  # [{field_key, field_label, field_type, default_value}]
  description: str  # 用户描述,如"某高层住宅1#楼,建筑面积12000㎡,框架结构"

class FillFieldsOut(BaseModel):
  """字段填充响应"""
  values: Dict[str, str]  # {field_key: filled_value}

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

def _call_ai(system_prompt: str, user_prompt: str, expect_json: bool = True) -> str:
  """调用 AI 并返回响应文本"""
  client = get_ai_client()
  resp = client.chat(messages=[
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": user_prompt},
  ])
  content = resp.get("content", "")
  if expect_json:
    # 尝试提取 JSON 块
    content = content.strip()
    if content.startswith("```"):
      lines = content.split("\n")
      start = next((i for i, l in enumerate(lines) if "```" in l), -1)
      end = next((i for i in range(start + 1, len(lines)) if "```" in lines[i]), len(lines))
      if start >= 0:
        content = "\n".join(lines[start + 1:end]).strip()
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