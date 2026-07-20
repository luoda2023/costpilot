"""
造价通 - 统一 AI 客户端(多 Provider 适配层)

支持:
  - DeepSeek / Qwen(通义) / Zhipu(智谱) / Moonshot(KIMI) / OpenAI
  - 任何 OpenAI 兼容的 /v1/chat/completions 接口
  - Ollama 本地(可选,无密钥)
  - Function Call(OpenAI tools 标准格式)

设计原则:
  ① 不绑定任何厂商,切换 provider 只改 config.yaml
  ② 统一响应: 返回 {content, tool_calls, raw}
  ③ 流式/非流式 两种调用模式
"""
import json
from typing import List, Dict, Optional, Any
import requests

from packages.server.config import get_config


# ---------------------------------------------------------------------------
# 自定义异常
# ---------------------------------------------------------------------------

class AIClientError(Exception):
    """AI 调用异常"""


class AIConfigError(AIClientError):
    """AI 配置异常(如 base_url / api_key 缺失)"""


# ---------------------------------------------------------------------------
# 统一 AI 客户端
# ---------------------------------------------------------------------------

class AIClient:
    """
    OpenAI 兼容统一客户端

    用法:
        from packages.server.ai.client import get_ai_client
        client = get_ai_client()
        resp = client.chat(messages=[{"role":"user","content":"你好"}])
        print(resp["content"])
    """

    def __init__(self, **overrides):
        """
        overrides: 可显式覆盖任意配置项(base_url/api_key/model/temperature/max_tokens/timeout)
        """
        cfg = get_config().ai.resolved()
        # 合并 override
        self.provider = overrides.get("provider", cfg["provider"])
        self.base_url = overrides.get("base_url", cfg["base_url"])
        self.api_key = overrides.get("api_key", cfg["api_key"])
        self.model = overrides.get("model", cfg["model"])
        self.temperature = overrides.get("temperature", cfg["temperature"])
        self.max_tokens = overrides.get("max_tokens", cfg["max_tokens"])
        self.timeout = overrides.get("timeout", cfg["timeout"])

        # Ollama 不需要 api_key
        if self.provider != "ollama" and not self.api_key:
            raise AIConfigError(
                f"AI api_key 未配置。请在 config.yaml 的 ai.api_key 填入 {self.provider} 的密钥,"
                f"或设置环境变量 COSTPILOT_AI_API_KEY。"
            )

        if not self.base_url:
            raise AIConfigError(f"AI base_url 未配置")

        if not self.model:
            raise AIConfigError(f"AI model 未配置")

    # -----------------------------------------------------------------------
    # 非流式调用
    # -----------------------------------------------------------------------

    def chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        tool_choice: Optional[str] = "auto",
    ) -> Dict[str, Any]:
        """
        非流式 chat 调用

        返回:
            {
              "content":      str,                  # 助手回复文本
              "tool_calls":   List[Dict] | None,    # 工具调用列表
              "finish_reason": str,                 # stop / tool_calls / length
              "raw":          dict,                 # 原始响应(调试用)
            }
        """
        url = self._endpoint()
        headers = self._headers()
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": False,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = tool_choice

        try:
            r = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
        except requests.RequestException as e:
            raise AIClientError(f"AI HTTP 请求失败: {e}") from e

        if r.status_code != 200:
            raise AIClientError(
                f"AI 调用失败 [{r.status_code}]: {r.text[:500]}"
            )

        data = r.json()
        msg = data["choices"][0]["message"]
        return {
            "content": msg.get("content") or "",
            "tool_calls": msg.get("tool_calls"),
            "finish_reason": data["choices"][0].get("finish_reason"),
            "raw": data,
        }

    # -----------------------------------------------------------------------
    # 流式调用(返回生成器)
    # -----------------------------------------------------------------------

    def chat_stream(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
    ):
        """
        流式调用,逐 token 返回 content 字符串

        用法:
            for chunk in client.chat_stream(messages):
                print(chunk, end="", flush=True)
        """
        url = self._endpoint()
        headers = self._headers()
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": True,
        }
        if tools:
            payload["tools"] = tools

        with requests.post(url, json=payload, headers=headers, timeout=self.timeout, stream=True) as r:
            if r.status_code != 200:
                raise AIClientError(f"AI 流式调用失败 [{r.status_code}]: {r.text[:500]}")
            for line in r.iter_lines():
                if not line:
                    continue
                line = line.decode("utf-8")
                if line.startswith("data: "):
                    payload_str = line[6:]
                    if payload_str.strip() == "[DONE]":
                        break
                    try:
                        chunk = json.loads(payload_str)
                        delta = chunk["choices"][0].get("delta", {})
                        if delta.get("content"):
                            yield delta["content"]
                        # tool_calls 流式增量此处简化处理,实际生产需合并累积
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue

    # -----------------------------------------------------------------------
    # 私有辅助
    # -----------------------------------------------------------------------

    def _endpoint(self) -> str:
        """拼出 /v1/chat/completions 端点"""
        url = self.base_url.rstrip("/")
        if not url.endswith("/chat/completions"):
            url = f"{url}/chat/completions"
        return url

    def _headers(self) -> Dict[str, str]:
        """通用请求头"""
        h = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.provider == "ollama" or "127.0.0.1:11434" in self.base_url:
            return h
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    # -----------------------------------------------------------------------
    # 工具函数
    # -----------------------------------------------------------------------

    def test_connection(self) -> Dict[str, Any]:
        """测试连接是否可用,返回 {"ok": bool, "msg": str}"""
        try:
            resp = self.chat(
                messages=[{"role": "user", "content": "你好,这是一个连接测试,请回复\'测试通过\'"}],
            )
            return {
                "ok": True,
                "msg": f"连接成功 | Provider: {self.provider} | Model: {self.model}",
                "reply": resp["content"][:200],
            }
        except Exception as e:
            return {"ok": False, "msg": str(e)}


# ---------------------------------------------------------------------------
# 单例
# ---------------------------------------------------------------------------

_client: Optional[AIClient] = None


def get_ai_client(**overrides) -> AIClient:
    """获取全局 AI 客户端单例"""
    global _client
    if _client is None or overrides:
        _client = AIClient(**overrides)
    return _client


def reset_ai_client():
    """重置单例(config.yaml 改后用)"""
    global _client
    _client = None


# ---------------------------------------------------------------------------
# 自测
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("AI 客户端 - 自测")
    print("=" * 60)

    try:
        client = get_ai_client()
        result = client.test_connection()
        if result["ok"]:
            print("✅", result["msg"])
            print("   回复:", result["reply"])
        else:
            print("❌", result["msg"])
    except AIConfigError as e:
        print(f"⚠ 配置未就绪: {e}")
        print()
        print("配置提示:")
        print("  1. 编辑 H:\\AI-model\\造价通\\config.yaml")
        print("  2. 在 ai.api_key 填入对应 provider 的密钥")
        print("  3. 重新运行本测试")
    except Exception as e:
        print(f"❌ 异常: {e}")
