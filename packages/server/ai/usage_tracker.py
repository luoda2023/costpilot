"""
工程助手 - AI 使用次数跟踪

免费 100 次试用，使用 JSON 文件持久化。
文件路径: %APPDATA%/engineering-assistant/usage.json

用法:
 from packages.server.ai.usage_tracker import UsageTracker
 tracker = UsageTracker()
 tracker.increment("text")  # text | image
 remaining = tracker.get_remaining("text")
"""
import os
import json
import sys
from pathlib import Path
from typing import Dict, Optional


def _usage_path() -> Path:
	"""确定 usage.json 的存储路径（与 config.yaml 同目录）"""
	data_dir = os.environ.get("ENGINEERING_ASSISTANT_DATA_DIR")
	if data_dir:
		return Path(data_dir) / "usage.json"
	if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
		return Path(sys.executable).resolve().parent / "usage.json"
	return Path(__file__).resolve().parent.parent.parent.parent / "usage.json"


USAGE_PATH = _usage_path()
MAX_FREE_CALLS = 100

# 内置免费试用密钥（用于判断是否正在使用免费额度）
_FREE_TRIAL_API_KEY = "sk-proxy-local-51f5bd4b9797f2620bc55460946802711cf7312b38c24794"


class UsageTracker:
	"""AI 使用次数跟踪器"""

	_instance: Optional["UsageTracker"] = None

	def __new__(cls):
		if cls._instance is None:
			cls._instance = super().__new__(cls)
			cls._instance._data = None
		return cls._instance

	def _load(self) -> Dict:
		"""从 JSON 文件加载使用数据"""
		if self._data is not None:
			return self._data
		if USAGE_PATH.exists():
			try:
				self._data = json.loads(USAGE_PATH.read_text(encoding="utf-8"))
			except (json.JSONDecodeError, OSError):
				self._data = {}
		else:
			self._data = {}
		# 确保默认字段存在
		self._data.setdefault("text_ai_calls", 0)
		self._data.setdefault("image_ai_calls", 0)
		self._data.setdefault("max_free_calls", MAX_FREE_CALLS)
		return self._data

	def _save(self):
		"""保存使用数据到 JSON 文件"""
		try:
			USAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
			USAGE_PATH.write_text(
				json.dumps(self._data, ensure_ascii=False, indent=2),
				encoding="utf-8",
			)
		except OSError:
			pass  # 写失败不阻塞调用

	def increment(self, call_type: str = "text"):
		"""
		递增使用次数

		参数:
			call_type: "text" 或 "image"
		"""
		data = self._load()
		key = f"{call_type}_ai_calls"
		data[key] = data.get(key, 0) + 1
		self._save()

	def get_remaining(self, call_type: str = "text") -> int:
		"""获取剩余免费次数"""
		data = self._load()
		key = f"{call_type}_ai_calls"
		used = data.get(key, 0)
		max_calls = data.get("max_free_calls", MAX_FREE_CALLS)
		remaining = max_calls - used
		return max(remaining, 0)

	def get_usage(self) -> Dict:
		"""获取完整使用情况"""
		data = self._load()
		text_used = data.get("text_ai_calls", 0)
		image_used = data.get("image_ai_calls", 0)
		max_calls = data.get("max_free_calls", MAX_FREE_CALLS)
		return {
			"text_ai_calls": text_used,
			"image_ai_calls": image_used,
			"max_free_calls": max_calls,
			"text_remaining": max(max_calls - text_used, 0),
			"image_remaining": max(max_calls - image_used, 0),
		}

	def is_free_trial_active(self, api_key: str) -> bool:
		"""判断是否正在使用免费密钥"""
		if not api_key:
			return False
		return api_key == _FREE_TRIAL_API_KEY

	def check_and_increment(self, api_key: str, call_type: str = "text"):
		"""
		检查免费次数并递增（如果使用免费密钥）

		返回:
			(ok: bool, msg: str, remaining: int)
		"""
		if not self.is_free_trial_active(api_key):
			return True, "使用自定义密钥，无限制", 9999

		remaining = self.get_remaining(call_type)
		if remaining <= 0:
			return False, f"免费试用次数已用完（{MAX_FREE_CALLS}/{MAX_FREE_CALLS}），请在系统设置中配置自己的 API Key", 0

		self.increment(call_type)
		new_remaining = self.get_remaining(call_type)
		return True, f"免费试用剩余 {new_remaining}/{MAX_FREE_CALLS} 次", new_remaining