"""阿里云 SMS 适配器：短信通知"""
import logging
from app.adapters.base import SMSAdapter
from app.config import settings

logger = logging.getLogger("warehouse.adapter.sms")


class AliyunSMSAdapter(SMSAdapter):
    """阿里云短信服务适配器"""

    def __init__(self):
        self.access_key_id = settings.SMS_ACCESS_KEY_ID
        self.access_key_secret = settings.SMS_ACCESS_KEY_SECRET
        self.sign_name = settings.SMS_SIGN_NAME
        self.template_code = settings.SMS_TEMPLATE_CODE

    @property
    def _configured(self) -> bool:
        return bool(self.access_key_id and self.access_key_secret and self.sign_name)

    async def send_notification(self, phone: str, template_code: str = "", params: dict = None) -> bool:
        if not self._configured:
            logger.warning("SMS 未配置，跳过发送")
            return False

        params = params or {}
        code = template_code or self.template_code

        try:
            import httpx
            import json

            # 阿里云 SMS 发送接口（简化版，生产环境应使用 SDK 或完整签名）
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    "https://dysmsapi.aliyuncs.com/",
                    data={
                        "PhoneNumbers": phone,
                        "SignName": self.sign_name,
                        "TemplateCode": code,
                        "TemplateParam": json.dumps(params),
                    },
                )
                if resp.status_code == 200:
                    logger.info(f"SMS 发送成功: {phone}")
                    return True
                else:
                    logger.error(f"SMS 发送失败: {resp.status_code} {resp.text}")
                    return False
        except Exception as e:
            logger.error(f"SMS 发送异常: {e}")
            return False
