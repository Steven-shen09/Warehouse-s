"""Kimi AI 适配器：前端页面生成、图像生成"""
import json
import logging
from typing import Optional
import httpx
from app.adapters.base import AIAdapter
from app.config import settings

logger = logging.getLogger("warehouse.adapter.kimi")


class KimiAdapter(AIAdapter):
    """Moonshot Kimi API 适配器 — 前端 UI 生成、图像生成"""

    def __init__(self):
        self.api_key = settings.KIMI_API_KEY
        self.base_url = settings.KIMI_BASE_URL.rstrip("/")
        self.chat_url = f"{self.base_url}/chat/completions"

    async def _chat(self, messages: list, temperature: float = 0.7, max_tokens: int = 4096) -> Optional[str]:
        """调用 Kimi Chat API"""
        if not self.api_key:
            logger.warning("Kimi API Key 未配置")
            return None

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    self.chat_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "moonshot-v1-auto",
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    logger.error(f"Kimi API 错误: {resp.status_code} {resp.text}")
                    return None
        except Exception as e:
            logger.error(f"Kimi API 调用异常: {e}")
            return None

    # ── Kimi 主责：前端页面生成 ─────────────────────────────────

    async def generate_page_template(self, description: str, context: dict | None = None) -> Optional[str]:
        """根据自然语言描述生成前端页面 HTML/CSS 片段"""
        system_prompt = (
            "你是一个前端设计专家，擅长 Flat Design 风格。"
            "根据用户描述生成可直接嵌入 Jinja2 模板的 HTML 片段（含内联 CSS）。"
            "要求：使用语义化标签、支持暗色模式（通过 prefers-color-scheme 媒体查询）、"
            "不引入任何外部 CDN 依赖、所有资源路径使用 /static/ 前缀。"
            "只输出 HTML/CSS 代码，不要包含 markdown 代码块标记，不要额外解释。"
        )

        user_content = f"请生成以下页面的 HTML/CSS 代码：{description}"
        if context:
            user_content += f"\n\n上下文信息：{json.dumps(context, ensure_ascii=False)}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]
        return await self._chat(messages, temperature=0.7, max_tokens=8192)

    async def generate_image(self, prompt: str, style: str = "flat") -> Optional[bytes]:
        """
        根据描述生成图片（占位）。
        Kimi 本身不提供图像生成 API，此处预留给实际图像生成服务接入。
        可通过替换此方法接入 DALL-E、Stable Diffusion 等。
        """
        logger.info(f"Kimi 不直接支持图像生成，尝试通过视觉模型返回 SVG 占位: {prompt[:50]}...")

        messages = [
            {
                "role": "system",
                "content": (
                    "你是一个 SVG 插画师。根据描述生成一段独立的 SVG 代码。"
                    "要求：Flat Design 风格、简洁配色、不需要外部字体或图片。"
                    "只输出 SVG 代码，不要 markdown 标记。"
                ),
            },
            {"role": "user", "content": f"请生成一张 SVG 插图：{prompt}，风格：{style}"},
        ]
        result = await self._chat(messages, temperature=0.8, max_tokens=4096)
        if result:
            # 尝试提取 SVG 标签内容
            import re
            match = re.search(r"<svg[\s\S]*?</svg>", result, re.IGNORECASE)
            if match:
                return match.group(0).encode("utf-8")
            # 如果整个返回就是 SVG，直接返回
            if result.strip().startswith("<svg"):
                return result.encode("utf-8")
        return None

    # ── 非主责方法：降级 ─────────────────────────────────────

    async def get_approval_suggestion(self, record_info: dict) -> Optional[str]:
        """Kimi 不负责审核建议，返回 None 让路由器降级到 DeepSeek"""
        return None

    async def detect_anomaly(self, records: list) -> list:
        """Kimi 不负责异常检测，返回空让路由器降级到 DeepSeek"""
        return []
