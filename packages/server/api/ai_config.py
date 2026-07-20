"""AI 配置管理 API

供前端"系统设置"页面:
  - GET  /api/v1/ai/config         查看当前 AI 配置(api_key 脱敏)
  - GET  /api/v1/ai/providers      列出内置 Provider
  - POST /api/v1/ai/test            测试连接
  - POST /api/v1/ai/switch          切换 provider + 重置客户端
"""
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from packages.server.config import get_config, reload_config
from packages.server.ai.client import get_ai_client, reset_ai_client, AIClientError, AIConfigError

router = APIRouter()


class AIConfigOut(BaseModel):
 provider: str
 base_url: str
 model: str
 temperature: float
 max_tokens: int
 timeout: int
 api_key_set: bool # 是否已设置(不返回明文)
 api_key_preview: str  # 脱敏预览
 lobechat_url: str = "http://localhost:3210"


class SwitchIn(BaseModel):
 provider: Optional[str] = None
 base_url: Optional[str] = None
 api_key: Optional[str] = None
 model: Optional[str] = None
 lobechat_url: Optional[str] = None


@router.get("/config", response_model=AIConfigOut)
def get_ai_config():
 """查看当前 AI 配置(api_key 脱敏)"""
 cfg = get_config().ai.resolved()
 key = cfg["api_key"]
 return AIConfigOut(
 provider=cfg["provider"],
 base_url=cfg["base_url"],
 model=cfg["model"],
 temperature=cfg["temperature"],
 max_tokens=cfg["max_tokens"],
 timeout=cfg["timeout"],
 api_key_set=bool(key),
 api_key_preview=(key[:6] + "***" + key[-4:]) if len(key) > 10 else ("***" if key else ""),
 lobechat_url=cfg.get("lobechat_url", "http://localhost:3210"),
 )


@router.get("/providers")
def list_providers():
    """列出所有内置 Provider"""
    cfg = get_config()
    return [
        {
            "name": name,
            "base_url": preset.get("base_url", ""),
            "default_model": preset.get("model", ""),
            "note": preset.get("note", ""),
            "needs_api_key": name != "ollama",
        }
        for name, preset in cfg.ai.presets.items()
    ]


@router.post("/test")
def test_ai_connection():
    """测试当前 AI 连接是否可用"""
    try:
        client = get_ai_client()
        return client.test_connection()
    except (AIConfigError, AIClientError) as e:
        return {"ok": False, "msg": str(e)}
    except Exception as e:
        return {"ok": False, "msg": f"未知异常: {e}"}


@router.post("/switch")
def switch_provider(s: SwitchIn):
    """切换 provider / 配置项后立即生效(写入运行时,不改 config.yaml)

    注: 持久化需用户手动编辑 config.yaml;这里只切换运行时
    """
    overrides = {}
    if s.provider:
        overrides["provider"] = s.provider
    if s.base_url:
        overrides["base_url"] = s.base_url
    if s.api_key:
        overrides["api_key"] = s.api_key
    if s.model:
        overrides["model"] = s.model

    reset_ai_client()
    try:
        client = get_ai_client(**overrides)
        return {
            "ok": True,
            "msg": f"已切换到 {client.provider} / {client.model}",
            "current": {
                "provider": client.provider,
                "base_url": client.base_url,
                "model": client.model,
            },
        }
    except (AIConfigError, AIClientError) as e:
        return {"ok": False, "msg": str(e)}


@router.post("/reload")
def reload_yaml():
    """重新从 config.yaml 加载配置(用户编辑后调用)"""
    reload_config()
    reset_ai_client()
    return {"ok": True, "msg": "配置已重新加载"}
