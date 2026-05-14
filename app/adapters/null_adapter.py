"""空适配器：当第三方服务未配置时的降级桩实现"""
import logging
from typing import Optional
from app.adapters.base import AIAdapter, OSSAdapter, SMSAdapter

logger = logging.getLogger("warehouse.adapter")


class NullAIAdapter(AIAdapter):
    """空 AI 适配器：记录日志但不调用任何外部 API"""

    async def get_approval_suggestion(self, record_info: dict) -> Optional[str]:
        logger.info(f"[NullAI] 跳过 AI 审核建议（未配置 DeepSeek）")
        return None

    async def detect_anomaly(self, records: list) -> list:
        logger.info(f"[NullAI] 跳过异常检测（未配置 DeepSeek）")
        return []


class NullOSSAdapter(OSSAdapter):
    """空 OSS 适配器：文件存本地"""

    async def upload_image(self, file_data: bytes, filename: str) -> Optional[str]:
        logger.info(f"[NullOSS] 跳过云上传，文件仅存本地: {filename}")
        return f"/static/img/{filename}"

    async def delete_image(self, url: str) -> bool:
        logger.info(f"[NullOSS] 跳过云删除: {url}")
        return True


class NullSMSAdapter(SMSAdapter):
    """空 SMS 适配器：仅记录日志"""

    async def send_notification(self, phone: str, template_code: str, params: dict) -> bool:
        logger.info(f"[NullSMS] 模拟发送短信到 {phone}，模板={template_code}，参数={params}")
        return True
