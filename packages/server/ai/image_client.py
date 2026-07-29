"""
工程助手 - 图片 AI 客户端

支持:
  - OpenAI DALL-E 3 (标准 OpenAI 兼容)
  - 阿里云通义万相 (DashScope API)
  - 智谱 CogView (Zhipu API)

用法:
  from packages.server.ai.image_client import get_image_client
  client = get_image_client()
  result = client.generate("一个建筑工地的施工示意图, 风格: 简洁工程图")
  print(result["url"])  # 图片 URL 或 base64
"""
import json
import base64
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Optional, Dict, Any
from packages.server.config import get_config


class ImageClientError(Exception):
    """图片 AI 调用异常"""


def _create_session(timeout: int = 120) -> requests.Session:
    """创建带连接池和重试机制的 Session"""
    session = requests.Session()
    retry = Retry(
        total=2,
        backoff_factor=0.5,
        allowed_methods={"POST", "GET"},
        status_forcelist={429, 500, 502, 503, 504},
    )
    adapter = HTTPAdapter(
        pool_connections=4,
        pool_maxsize=8,
        max_retries=retry,
        pool_block=True,
    )
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


class ImageClient:
    """
    统一图片生成客户端

    支持三种后端:
      - openai: 标准 OpenAI /v1/images/generations
      - qwen: 阿里云通义万相
      - zhipu: 智谱 CogView
    """

    def __init__(self, **overrides):
        cfg = get_config().image_ai.resolved()
        self.provider = overrides.get("provider", cfg["provider"])
        self.base_url = overrides.get("base_url", cfg["base_url"])
        self.api_key = overrides.get("api_key", cfg["api_key"])
        self.model = overrides.get("model", cfg["model"])
        self.timeout = overrides.get("timeout", cfg["timeout"])
        self._session = _create_session(self.timeout)

        if not self.api_key:
            raise ImageClientError(
                f"图片 AI api_key 未配置。请在系统设置-图片AI中配置 {self.provider} 的密钥。"
            )

    def generate(self, prompt: str, size: str = "1024x1024") -> Dict[str, Any]:
        """
        生成图片

        参数:
          prompt: 图片描述
          size: 图片尺寸 (1024x1024 / 1024x1792 等)

        返回:
          {"url": str, "revised_prompt": str, "b64_json": str | None}
        """
        method_name = f"_generate_{self.provider}"
        method = getattr(self, method_name, None)
        if not method:
            raise ImageClientError(f"不支持的图片 AI provider: {self.provider}")
        return method(prompt, size)

    # -----------------------------------------------------------------------
    # OpenAI DALL-E 3
    # -----------------------------------------------------------------------

    def _generate_openai(self, prompt: str, size: str) -> Dict[str, Any]:
        url = (self.base_url.rstrip("/") + "/images/generations")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        payload = {
            "model": self.model or "dall-e-3",
            "prompt": prompt,
            "n": 1,
            "size": size,
        }
        try:
            r = self._session.post(url, json=payload, headers=headers, timeout=self.timeout)
        except requests.RequestException as e:
            raise ImageClientError(f"图片 AI HTTP 请求失败: {e}") from e

        if r.status_code != 200:
            raise ImageClientError(f"图片 AI 调用失败 [{r.status_code}]: {r.text[:500]}")

        data = r.json()
        img_data = data["data"][0]
        return {
            "url": img_data.get("url"),
            "b64_json": img_data.get("b64_json"),
            "revised_prompt": img_data.get("revised_prompt", prompt),
        }

    # -----------------------------------------------------------------------
    # 阿里云通义万相
    # -----------------------------------------------------------------------

    def _generate_qwen(self, prompt: str, size: str) -> Dict[str, Any]:
        url = (self.base_url.rstrip("/") + "/api/v1/services/aigc/text2image/image-synthesis")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "X-DashScope-Async": "enable",
        }
        size_qwen = size.replace("x", "*")
        payload = {
            "model": self.model or "wanx-v1",
            "input": {
                "prompt": prompt,
                "negative_prompt": "低质量,模糊,变形,水印",
            },
            "parameters": {
                "size": size_qwen,
                "n": 1,
            },
        }
        try:
            r = self._session.post(url, json=payload, headers=headers, timeout=self.timeout)
        except requests.RequestException as e:
            raise ImageClientError(f"通义万相 HTTP 请求失败: {e}") from e

        if r.status_code != 200:
            raise ImageClientError(f"通义万相调用失败 [{r.status_code}]: {r.text[:500]}")

        data = r.json()
        task_id = data.get("output", {}).get("task_id")
        if task_id:
            return self._poll_qwen(task_id, headers)
        return {"url": None, "b64_json": None, "revised_prompt": prompt}

    def _poll_qwen(self, task_id: str, headers: dict, max_retries: int = 30) -> Dict[str, Any]:
        """轮询通义万相异步任务"""
        import time
        url = (self.base_url.rstrip("/") + f"/api/v1/tasks/{task_id}")
        for _ in range(max_retries):
            try:
                r = self._session.get(url, headers=headers, timeout=30)
                if r.status_code == 200:
                    data = r.json()
                    status = data.get("output", {}).get("task_status")
                    if status == "SUCCEEDED":
                        results = data.get("output", {}).get("results", [])
                        if results:
                            img_url = results[0].get("url")
                            if img_url:
                                return {"url": img_url, "b64_json": None, "revised_prompt": ""}
                        break
                    elif status == "FAILED":
                        raise ImageClientError(f"通义万相生成失败: {data.get('output', {}).get('message', '')}")
                time.sleep(2)
            except requests.RequestException:
                time.sleep(2)
        return {"url": None, "b64_json": None, "revised_prompt": ""}

    # -----------------------------------------------------------------------
    # 智谱 CogView
    # -----------------------------------------------------------------------

    def _generate_zhipu(self, prompt: str, size: str) -> Dict[str, Any]:
        url = (self.base_url.rstrip("/") + "/images/generations")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        payload = {
            "model": self.model or "cogview-3",
            "prompt": prompt,
            "size": size,
            "n": 1,
        }
        try:
            r = self._session.post(url, json=payload, headers=headers, timeout=self.timeout)
        except requests.RequestException as e:
            raise ImageClientError(f"智谱 CogView HTTP 请求失败: {e}") from e

        if r.status_code != 200:
            raise ImageClientError(f"智谱 CogView 调用失败 [{r.status_code}]: {r.text[:500]}")

        data = r.json()
        img_data = data["data"][0]
        return {
            "url": img_data.get("url"),
            "b64_json": None,
            "revised_prompt": prompt,
        }


# ---------------------------------------------------------------------------
# 单例
# ---------------------------------------------------------------------------

_image_client: Optional[ImageClient] = None


def get_image_client(**overrides) -> ImageClient:
    global _image_client
    if overrides:
        return ImageClient(**overrides)
    if _image_client is None:
        _image_client = ImageClient()
    return _image_client


def reset_image_client():
    """重置单例(config.yaml 改后用)"""
    global _image_client
    _image_client = None