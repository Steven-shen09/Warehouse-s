"""DeepSeek AI 适配器：智能审核建议、异常检测"""
import json
import logging
from typing import Optional
import httpx
from app.adapters.base import AIAdapter
from app.config import settings

logger = logging.getLogger("warehouse.adapter.ai")


class DeepSeekAdapter(AIAdapter):
    """DeepSeek Chat API 适配器"""

    def __init__(self):
        self.api_key = settings.DEEPSEEK_API_KEY
        self.base_url = settings.DEEPSEEK_BASE_URL.rstrip("/")
        self.chat_url = f"{self.base_url}/chat/completions"

    async def _chat(self, messages: list) -> Optional[str]:
        """调用 DeepSeek Chat API"""
        if not self.api_key:
            logger.warning("DeepSeek API Key 未配置")
            return None

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    self.chat_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "deepseek-chat",
                        "messages": messages,
                        "temperature": 0.3,
                        "max_tokens": 500,
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    logger.error(f"DeepSeek API 错误: {resp.status_code} {resp.text}")
                    return None
        except Exception as e:
            logger.error(f"DeepSeek API 调用异常: {e}")
            return None

    async def get_approval_suggestion(self, record_info: dict) -> Optional[str]:
        """基于租借记录信息生成审核建议"""
        messages = [
            {"role": "system", "content": "你是一个物品管理系统的审核助手。根据租借信息给出简短、客观的审核建议（30字以内）。只需输出建议内容，不需要额外解释。"},
            {"role": "user", "content": f"请审核以下租借申请：{json.dumps(record_info, ensure_ascii=False)}"},
        ]
        return await self._chat(messages)

    async def detect_anomaly(self, records: list) -> list:
        """检测异常租借记录"""
        if not records:
            return []

        messages = [
            {"role": "system", "content": "你是一个异常检测助手。分析以下租借记录，指出其中异常的模式（如：同一用户短期内大量借出、超出正常数量、逾期异常等）。以 JSON 数组格式返回异常记录的 ID 列表，如 [1, 3, 5]。仅输出 JSON 数组。"},
            {"role": "user", "content": f"请分析以下记录中的异常：{json.dumps(records, ensure_ascii=False)}"},
        ]
        result = await self._chat(messages)
        if result:
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                logger.warning(f"DeepSeek 异常检测返回格式错误: {result}")
                return []
        return []
