"""多模型 AI 路由器：根据任务类型分发到最优模型"""
import logging
from typing import Optional

from app.adapters.base import AIAdapter
from app.adapters.ai_adapter import DeepSeekAdapter
from app.adapters.kimi_adapter import KimiAdapter
from app.adapters.null_adapter import NullAIAdapter
from app.config import settings

logger = logging.getLogger("warehouse.router.ai")


class MultiAIRouter:
    """
    AI 路由器 — 按能力路由到不同模型。

    路由策略：
    - 审核建议 / 异常检测  →  DeepSeek（主） → Kimi（备） → 降级
    - 前端生成 / 图像生成  →  Kimi（主）     → DeepSeek（备） → 降级

    未配置 API Key 的适配器自动跳过。
    """

    def __init__(self):
        self._deepseek: Optional[AIAdapter] = None
        self._kimi: Optional[AIAdapter] = None
        self._null: Optional[AIAdapter] = None

    @property
    def deepseek(self) -> AIAdapter:
        if self._deepseek is None:
            self._deepseek = DeepSeekAdapter() if settings.DEEPSEEK_API_KEY else NullAIAdapter()
        return self._deepseek

    @property
    def kimi(self) -> AIAdapter:
        if self._kimi is None:
            self._kimi = KimiAdapter() if settings.KIMI_API_KEY else NullAIAdapter()
        return self._kimi

    @property
    def null(self) -> AIAdapter:
        if self._null is None:
            self._null = NullAIAdapter()
        return self._null

    # ── 审核与异常检测（DeepSeek 主责）─────────────────────────────

    async def get_approval_suggestion(self, record_info: dict) -> Optional[str]:
        """获取审核建议：DeepSeek → Kimi → 降级"""
        result = await self.deepseek.get_approval_suggestion(record_info)
        if result is not None:
            return result
        logger.info("DeepSeek 审核建议失败，尝试 Kimi 降级")
        result = await self.kimi.get_approval_suggestion(record_info)
        if result is not None:
            return result
        return await self.null.get_approval_suggestion(record_info)

    async def detect_anomaly(self, records: list) -> list:
        """异常检测：DeepSeek → Kimi → 降级"""
        result = await self.deepseek.detect_anomaly(records)
        if result:
            return result
        logger.info("DeepSeek 异常检测失败，尝试 Kimi 降级")
        result = await self.kimi.detect_anomaly(records)
        if result:
            return result
        return await self.null.detect_anomaly(records)

    # ── 前端生成与图像（Kimi 主责）─────────────────────────────────

    async def generate_page_template(self, description: str, context: dict | None = None) -> Optional[str]:
        """生成前端页面：Kimi → DeepSeek → 降级"""
        result = await self.kimi.generate_page_template(description, context)
        if result is not None:
            return result
        logger.info("Kimi 页面生成失败，尝试 DeepSeek 降级")
        result = await self.deepseek.generate_page_template(description, context)
        if result is not None:
            return result
        return await self.null.generate_page_template(description, context)

    async def generate_image(self, prompt: str, style: str = "flat") -> Optional[bytes]:
        """生成图像：Kimi → DeepSeek → 降级"""
        result = await self.kimi.generate_image(prompt, style)
        if result is not None:
            return result
        logger.info("Kimi 图像生成失败，尝试 DeepSeek 降级")
        result = await self.deepseek.generate_image(prompt, style)
        if result is not None:
            return result
        return await self.null.generate_image(prompt, style)


# 全局单例
_router: Optional[MultiAIRouter] = None


def get_ai_router() -> MultiAIRouter:
    """获取 AI 路由器全局单例"""
    global _router
    if _router is None:
        _router = MultiAIRouter()
    return _router
