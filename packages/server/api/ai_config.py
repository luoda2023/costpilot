"""AI 配置管理 API

供前端"系统设置"页面:
  - GET  /api/v1/ai/config 查看当前 AI 配置(api_key 脱敏)
  - GET  /api/v1/ai/providers 列出内置 Provider
  - POST /api/v1/ai/test 测试连接
  - POST /api/v1/ai/switch 切换 AI 配置(持久化到 config.yaml)
  - GET  /api/v1/ai/image-config 查看图片 AI 配置
  - POST /api/v1/ai/image-switch 切换图片 AI 配置
  - POST /api/v1/ai/reload 从文件重载
"""
from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel
import yaml

from packages.server.config import get_config, reload_config, CONFIG_PATH
from packages.server.ai.client import get_ai_client, reset_ai_client, AIClientError, AIConfigError

router = APIRouter()


class AIConfigOut(BaseModel):
	provider: str
	base_url: str
	model: str
	temperature: float
	max_tokens: int
	timeout: int
	api_key_set: bool
	api_key_preview: str
	lobechat_url: str = "http://localhost:3210"
	is_builtin: bool = False  # 是否使用内置免费配置


class ImageAIConfigOut(BaseModel):
	provider: str
	base_url: str
	model: str
	timeout: int
	api_key_set: bool
	api_key_preview: str
	is_builtin: bool = False  # 是否使用内置免费配置

class SwitchIn(BaseModel):
 provider: Optional[str] = None
 base_url: Optional[str] = None
 api_key: Optional[str] = None
 model: Optional[str] = None
 temperature: Optional[float] = None
 max_tokens: Optional[int] = None
 timeout: Optional[int] = None
 lobechat_url: Optional[str] = None

class ImageSwitchIn(BaseModel):
 provider: Optional[str] = None
 base_url: Optional[str] = None
 api_key: Optional[str] = None
 model: Optional[str] = None
 timeout: Optional[int] = None

def _mask_key(key: str) -> str:
 if not key:
  return "(未设置)"
 if len(key) > 10:
  return key[:6] + "***" + key[-4:]
 return "***"

def _write_yaml_section(raw: dict, section: str, data: dict):
 """写入 YAML 配置段"""
 if section not in raw:
  raw[section] = {}
 for k, v in data.items():
  if v is not None:
   raw[section][k] = v
 CONFIG_PATH.write_text(yaml.dump(raw, allow_unicode=True, default_flow_style=False), encoding="utf-8")
 reload_config()

@router.get("/config", response_model=AIConfigOut)
def get_ai_config():
	"""查看当前 AI 配置(api_key 脱敏，内置模式隐藏参数)"""
	cfg = get_config()
	raw = cfg.ai.resolved()
	is_builtin = cfg.ai.is_builtin()
	key = raw["api_key"]
	return AIConfigOut(
		provider=raw["provider"],
		# 内置模式不暴露具体参数
		base_url="(系统内置)" if is_builtin else raw["base_url"],
		model="(系统内置)" if is_builtin else raw["model"],
		temperature=raw["temperature"],
		max_tokens=raw["max_tokens"],
		timeout=raw["timeout"],
		api_key_set=bool(key),
		api_key_preview="(系统内置)" if is_builtin else _mask_key(key),
		lobechat_url=raw.get("lobechat_url", "http://localhost:3210"),
		is_builtin=is_builtin,
	)

@router.get("/image-config", response_model=ImageAIConfigOut)
def get_image_ai_config():
	"""查看图片 AI 配置（内置模式隐藏参数）"""
	cfg = get_config()
	is_builtin = cfg.image_ai.is_builtin()
	raw = cfg.image_ai.resolved()
	key = raw["api_key"]
	return ImageAIConfigOut(
		provider=raw["provider"],
		base_url="(系统内置)" if is_builtin else raw["base_url"],
		model="(系统内置)" if is_builtin else raw["model"],
		timeout=raw["timeout"],
		api_key_set=bool(key),
		api_key_preview="(系统内置)" if is_builtin else _mask_key(key),
		is_builtin=is_builtin,
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
 """切换 AI provider / 配置项后立即生效(写入 config.yaml 持久化)"""
 if CONFIG_PATH.exists():
  raw = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
 else:
  raw = {}
 data = {k: v for k, v in {
  "provider": s.provider,
  "base_url": s.base_url,
  "api_key": s.api_key,
  "model": s.model,
  "temperature": s.temperature,
  "max_tokens": s.max_tokens,
  "timeout": s.timeout,
  "lobechat_url": s.lobechat_url,
 }.items() if v is not None}
 _write_yaml_section(raw, "ai", data)
 reset_ai_client()
 try:
  client = get_ai_client()
  return {
   "ok": True,
   "msg": f"已切换到 {client.provider} / {client.model} (已保存到 config.yaml)",
   "current": {
    "provider": client.provider,
    "base_url": client.base_url,
    "model": client.model,
   },
  }
 except (AIConfigError, AIClientError) as e:
  return {"ok": False, "msg": str(e)}

@router.post("/image-switch")
def switch_image_provider(s: ImageSwitchIn):
 """切换图片 AI provider / 配置项后立即生效(写入 config.yaml 持久化)"""
 if CONFIG_PATH.exists():
  raw = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
 else:
  raw = {}
 data = {k: v for k, v in {
  "provider": s.provider,
  "base_url": s.base_url,
  "api_key": s.api_key,
  "model": s.model,
  "timeout": s.timeout,
 }.items() if v is not None}
 _write_yaml_section(raw, "image_ai", data)
 return {"ok": True, "msg": "图片 AI 配置已保存"}

@router.post("/reload")
def reload_yaml():
 """重新从 config.yaml 加载配置(用户编辑后调用)"""
 reload_config()
 reset_ai_client()
 return {"ok": True, "msg": "配置已重新加载"}

@router.get("/usage")
def get_ai_usage():
	 """获取 AI 使用情况（免费试用剩余次数）"""
	 try:
		 from packages.server.ai.usage_tracker import UsageTracker
		 tracker = UsageTracker()
		 return tracker.get_usage()
	 except ImportError:
		 return {"text_ai_calls": 0, "image_ai_calls": 0, "max_free_calls": 100, "text_remaining": 100, "image_remaining": 100, "note": "使用次数追踪模块未加载"}