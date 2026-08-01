"""
工程助手 - 自定义 AI 配置管理 API

用户可以在系统设置中新增/编辑/删除自定义 AI 配置。
存储到 %APPDATA%/engineering-assistant/custom_ai_configs.json

端点:
 GET  /api/v1/ai/custom-configs - 列出所有自定义配置
 POST /api/v1/ai/custom-configs - 新增
 PUT  /api/v1/ai/custom-configs/{id} - 修改
 DELETE /api/v1/ai/custom-configs/{id} - 删除
"""
import os
import json
import sys
import uuid
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


def _configs_path() -> Path:
    """确定自定义配置存储路径（与 usage.json 同目录）"""
    data_dir = os.environ.get("ENGINEERING_ASSISTANT_DATA_DIR")
    if data_dir:
        return Path(data_dir) / "custom_ai_configs.json"
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys.executable).resolve().parent / "custom_ai_configs.json"
    return Path(__file__).resolve().parent.parent.parent.parent / "custom_ai_configs.json"


CONFIGS_PATH = _configs_path()


class CustomAIConfigIn(BaseModel):
    model: str
    base_url: str
    api_key: str = ""
    temperature: float = 0.3
    max_tokens: int = 4096
    timeout: int = 120


class CustomAIConfigOut(BaseModel):
    id: str
    model: str
    base_url: str
    api_key: str
    temperature: float
    max_tokens: int
    timeout: int


def _load_configs() -> list:
    """加载自定义配置列表"""
    if CONFIGS_PATH.exists():
        try:
            return json.loads(CONFIGS_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []
    return []


def _save_configs(configs: list):
    """保存自定义配置列表"""
    try:
        CONFIGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONFIGS_PATH.write_text(
            json.dumps(configs, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError:
        pass


@router.get("", response_model=List[CustomAIConfigOut])
def list_custom_configs():
    """列出所有自定义 AI 配置"""
    configs = _load_configs()
    # 返回时脱敏 api_key
    result = []
    for c in configs:
        c_out = dict(c)
        key = c_out.get("api_key", "")
        if key and len(key) > 10:
            c_out["api_key"] = key[:6] + "***" + key[-4:]
        elif key:
            c_out["api_key"] = "***"
        result.append(c_out)
    return result


@router.post("", response_model=CustomAIConfigOut)
def create_custom_config(c: CustomAIConfigIn):
    """新增自定义 AI 配置"""
    configs = _load_configs()
    new_id = str(uuid.uuid4())[:8]
    new_config = {
        "id": new_id,
        "model": c.model,
        "base_url": c.base_url,
        "api_key": c.api_key,
        "temperature": c.temperature,
        "max_tokens": c.max_tokens,
        "timeout": c.timeout,
    }
    configs.append(new_config)
    _save_configs(configs)
    # 返回时脱敏
    out = dict(new_config)
    key = out.get("api_key", "")
    if key and len(key) > 10:
        out["api_key"] = key[:6] + "***" + key[-4:]
    elif key:
        out["api_key"] = "***"
    return out


@router.put("/{config_id}", response_model=CustomAIConfigOut)
def update_custom_config(config_id: str, c: CustomAIConfigIn):
    """修改自定义 AI 配置"""
    configs = _load_configs()
    for i, existing in enumerate(configs):
        if existing.get("id") == config_id:
            configs[i] = {
                "id": config_id,
                "model": c.model,
                "base_url": c.base_url,
                "api_key": c.api_key,
                "temperature": c.temperature,
                "max_tokens": c.max_tokens,
                "timeout": c.timeout,
            }
            _save_configs(configs)
            # 返回时脱敏
            out = dict(configs[i])
            key = out.get("api_key", "")
            if key and len(key) > 10:
                out["api_key"] = key[:6] + "***" + key[-4:]
            elif key:
                out["api_key"] = "***"
            return out
    raise HTTPException(status_code=404, detail="配置不存在")


@router.delete("/{config_id}")
def delete_custom_config(config_id: str):
    """删除自定义 AI 配置"""
    configs = _load_configs()
    new_configs = [c for c in configs if c.get("id") != config_id]
    if len(new_configs) == len(configs):
        raise HTTPException(status_code=404, detail="配置不存在")
    _save_configs(new_configs)
    return {"ok": True, "msg": "已删除"}


@router.post("/{config_id}/apply")
def apply_custom_config(config_id: str):
    """切换到指定的自定义配置（写入 config.yaml 的 ai 段并生效）"""
    configs = _load_configs()
    target = None
    for c in configs:
        if c.get("id") == config_id:
            target = c
            break
    if not target:
        raise HTTPException(status_code=404, detail="配置不存在")

    # 写入 config.yaml
    from packages.server.config import CONFIG_PATH
    import yaml
    from packages.server.api.ai_config import _write_yaml_section
    from packages.server.ai.client import get_ai_client, reset_ai_client

    if CONFIG_PATH.exists():
        raw = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
    else:
        raw = {}

    data = {
        "provider": "custom",
        "base_url": target["base_url"],
        "api_key": target["api_key"],
        "model": target["model"],
        "temperature": target["temperature"],
        "max_tokens": target["max_tokens"],
        "timeout": target["timeout"],
    }
    _write_yaml_section(raw, "ai", data)
    reset_ai_client()

    try:
        client = get_ai_client()
        return {
            "ok": True,
            "msg": f"已切换到 {client.model}",
            "current": {
                "provider": client.provider,
                "base_url": client.base_url,
                "model": client.model,
            },
        }
    except Exception as e:
        return {"ok": False, "msg": str(e)}