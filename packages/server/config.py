"""
造价通 - 配置加载器

读取项目根目录的 config.yaml, 提供全局访问入口:
    from packages.server.config import get_config
    cfg = get_config()
    cfg.ai.base_url / cfg.ai.api_key / cfg.ai.model

配置合并优先级(高 -> 低):
    1. 显式 ai.base_url / ai.api_key / ai.model          (用户填的)
    2. presets[provider]                                  (内置 Provider 默认)
    3. 全局默认值
"""
import os
import sys
from pathlib import Path
from typing import Any, Dict
from dataclasses import dataclass, field

import yaml

def _resolve_project_root() -> Path:
    """打包后 PyInstaller onefile: PROJECT_ROOT = exe 同目录
    开发模式: PROJECT_ROOT = 包上一级(项目根)
    """
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # PyInstaller onefile: 数据库 / config 写到 exe 同目录
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent.parent

PROJECT_ROOT = _resolve_project_root()
CONFIG_PATH = PROJECT_ROOT / "config.yaml"


@dataclass
class AIConfig:
    provider: str = "deepseek"
    base_url: str = ""
    api_key: str = ""
    model: str = ""
    temperature: float = 0.3
    max_tokens: int = 4096
    timeout: int = 120
    lobechat_url: str = "http://localhost:3210"
    presets: Dict[str, Dict[str, str]] = field(default_factory=dict)

    def resolved(self) -> Dict[str, Any]:
        """合并预置值与显式覆盖,返回最终生效配置"""
        preset = self.presets.get(self.provider, {})
        return {
            "provider": self.provider,
            "base_url": self.base_url or preset.get("base_url", ""),
            "api_key": self.api_key or os.environ.get("COSTPILOT_AI_API_KEY", ""),
            "model": self.model or preset.get("model", ""),
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "timeout": self.timeout,
            "lobechat_url": self.lobechat_url,
        }


@dataclass
class RAGConfig:
    embedding_model: str = "BAAI/bge-m3"
    embedding_dim: int = 1024
    chroma_dir: str = "data/chroma"
    chunk_size: int = 800
    chunk_overlap: int = 100
    chunk_min_size: int = 50
    top_k: int = 5
    score_threshold: float = 0.5


@dataclass
class DatabaseConfig:
    url: str = "sqlite:///data/sqlite/造价通.db"


@dataclass
class ServerConfig:
    host: str = "127.0.0.1"
    port: int = 8765


@dataclass
class AppConfig:
    ai: AIConfig = field(default_factory=AIConfig)
    rag: RAGConfig = field(default_factory=RAGConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    server: ServerConfig = field(default_factory=ServerConfig)
    knowledge_sources: list = field(default_factory=list)


# 全局单例
_config: AppConfig = None


def get_config() -> AppConfig:
    """全局配置访问入口"""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def load_config() -> AppConfig:
    """读取并解析 config.yaml"""
    if not CONFIG_PATH.exists():
        # 配置文件缺失,fallback 到默认(开发期容错)
        return AppConfig()

    raw = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}

    cfg = AppConfig(
        ai=AIConfig(
            provider=raw.get("ai", {}).get("provider", "deepseek"),
            base_url=raw.get("ai", {}).get("base_url", ""),
            api_key=raw.get("ai", {}).get("api_key", ""),
            model=raw.get("ai", {}).get("model", ""),
            temperature=raw.get("ai", {}).get("temperature", 0.3),
            max_tokens=raw.get("ai", {}).get("max_tokens", 4096),
            timeout=raw.get("ai", {}).get("timeout", 120),
            lobechat_url=raw.get("ai", {}).get("lobechat_url", "http://localhost:3210"),
            presets=raw.get("ai", {}).get("presets", {}),
        ),
        rag=RAGConfig(
            embedding_model=raw.get("rag", {}).get("embedding_model", "BAAI/bge-m3"),
            embedding_dim=raw.get("rag", {}).get("embedding_dim", 1024),
            chroma_dir=raw.get("rag", {}).get("chroma_dir", "data/chroma"),
            chunk_size=raw.get("rag", {}).get("chunk_size", 800),
            chunk_overlap=raw.get("rag", {}).get("chunk_overlap", 100),
            chunk_min_size=raw.get("rag", {}).get("chunk_min_size", 50),
            top_k=raw.get("rag", {}).get("top_k", 5),
            score_threshold=raw.get("rag", {}).get("score_threshold", 0.5),
        ),
        database=DatabaseConfig(
            url=raw.get("database", {}).get("url", "sqlite:///data/sqlite/造价通.db"),
        ),
        server=ServerConfig(
            host=raw.get("server", {}).get("host", "127.0.0.1"),
            port=raw.get("server", {}).get("port", 8765),
        ),
        knowledge_sources=raw.get("knowledge_sources", []),
    )
    return cfg


def reload_config():
    """强制重新读取(配置文件改动后调用)"""
    global _config
    _config = load_config()


# ---------------------------------------------------------------------------
# 自检
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    cfg = get_config()
    ai = cfg.ai.resolved()
    print("=" * 60)
    print("配置文件加载自:", CONFIG_PATH)
    print("=" * 60)
    print(f"AI Provider:    {ai['provider']}")
    print(f"AI base_url:    {ai['base_url']}")
    print(f"AI model:       {ai['model']}")
    print(f"AI api_key:     {'已设置' if ai['api_key'] else '⚠ 未设置'}")
    print(f"AI temperature: {ai['temperature']}")
    print()
    print(f"RAG embedding:  {cfg.rag.embedding_model}")
    print(f"RAG dims:       {cfg.rag.embedding_dim}")
    print(f"RAG chunk_size: {cfg.rag.chunk_size}")
    print(f"RAG top_k:      {cfg.rag.top_k}")
    print()
    print(f"数据库:         {cfg.database.url}")
    print(f"监听:           {cfg.server.host}:{cfg.server.port}")
    print()
    print(f"知识库源:")
    for s in cfg.knowledge_sources:
        print(f"  - {s.get('path')} | {s.get('description','')}")
