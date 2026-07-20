"""
造价通 - AI 推理封装

封装两类调用:
1. Ollama 本地 HTTP API (默认 http://127.0.0.1:11434)
2. 自定义 function call (后续扩展)

Phase 2 M6 接入;Phase 1 用占位回复(M1 阶段已实现于 api/chat.py)
"""
import os
import json
from typing import Optional, List, Dict
import requests

# Ollama 服务地址
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
# 模型
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b-instruct")


def check_ollama() -> bool:
    """检查 Ollama 服务是否可用"""
    try:
        r = requests.get(f"{OLLAMA_URL}/api/version", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


def list_local_models() -> List[str]:
    """列出 Ollama 已下载的模型"""
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        if r.status_code == 200:
            return [m["name"] for m in r.json().get("models", [])]
    except Exception:
        pass
    return []


def chat(messages: List[Dict], model: Optional[str] = None, stream: bool = False) -> str:
    """
    调用 Ollama chat 接口
    messages: [{role, content}, ...]
    返回: 助手回复文本
    """
    if not check_ollama():
        return "[Ollama 服务未运行] 请先执行 `ollama serve` 或安装 Ollama 桌面版"

    payload = {
        "model": model or OLLAMA_MODEL,
        "messages": messages,
        "stream": stream,
    }

    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json=payload,
            timeout=120,
            stream=stream,
        )
        r.raise_for_status()

        if stream:
            # 流式响应:逐行收集
            full_text = ""
            for line in r.iter_lines():
                if not line:
                    continue
                chunk = json.loads(line)
                if chunk.get("message", {}).get("content"):
                    full_text += chunk["message"]["content"]
            return full_text
        else:
            data = r.json()
            return data.get("message", {}).get("content", "")
    except requests.RequestException as e:
        return f"[Ollama 调用失败] {e}"


def chat_with_tools(messages: List[Dict], tools: List[Dict], model: Optional[str] = None) -> Dict:
    """
    Function call - Phase 2 M8
    tools: OpenAI function 格式
    返回: {content, tool_calls}
    """
    if not check_ollama():
        return {"content": "[Ollama 不可用]", "tool_calls": []}

    # 注:Ollama 0.1.x 已支持 tools 字段
    payload = {
        "model": model or OLLAMA_MODEL,
        "messages": messages,
        "tools": tools,
        "stream": False,
    }
    try:
        r = requests.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=120)
        r.raise_for_status()
        data = r.json()
        return {
            "content": data.get("message", {}).get("content", ""),
            "tool_calls": data.get("message", {}).get("tool_calls", []),
        }
    except requests.RequestException as e:
        return {"content": f"[tool call 失败] {e}", "tool_calls": []}


# 工具定义示例
TOOL_QUERY_PRICE = {
    "type": "function",
    "function": {
        "name": "query_price",
        "description": "查询综合单价",
        "parameters": {
            "type": "object",
            "properties": {
                "item_name": {"type": "string", "description": "项目名关键词"},
                "region": {"type": "string", "description": "地区,如 北京市"},
                "specialty": {"type": "string", "description": "专业,如 土建/市政"},
            },
            "required": ["item_name"],
        },
    },
}

TOOL_QUERY_FEE = {
    "type": "function",
    "function": {
        "name": "query_fee_rate",
        "description": "查询规费/措施费/税金费率",
        "parameters": {
            "type": "object",
            "properties": {
                "region": {"type": "string"},
                "fee_type": {"type": "string", "description": "规费/措施费/税金"},
            },
            "required": ["region"],
        },
    },
}

TOOL_QUERY_TEMPLATE = {
    "type": "function",
    "function": {
        "name": "query_template",
        "description": "查询文本格式谱骨架",
        "parameters": {
            "type": "object",
            "properties": {
                "doc_type": {"type": "string", "description": "可研报告/施组/方案/..."},
            },
            "required": ["doc_type"],
        },
    },
}

ALL_TOOLS = [TOOL_QUERY_PRICE, TOOL_QUERY_FEE, TOOL_QUERY_TEMPLATE]
