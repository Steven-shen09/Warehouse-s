"""阿里云 OSS 适配器：物品图片存储"""
import logging
from typing import Optional
from app.adapters.base import OSSAdapter
from app.config import settings

logger = logging.getLogger("warehouse.adapter.oss")


class AliyunOSSAdapter(OSSAdapter):
    """阿里云 OSS 对象存储适配器"""

    def __init__(self):
        self.access_key_id = settings.OSS_ACCESS_KEY_ID
        self.access_key_secret = settings.OSS_ACCESS_KEY_SECRET
        self.bucket = settings.OSS_BUCKET_NAME
        self.endpoint = settings.OSS_ENDPOINT

    @property
    def _configured(self) -> bool:
        return bool(self.access_key_id and self.access_key_secret and self.bucket)

    async def upload_image(self, file_data: bytes, filename: str) -> Optional[str]:
        if not self._configured:
            logger.warning("OSS 未配置，跳过上传")
            return None

        # 使用 httpx 调用 OSS REST API
        try:
            import httpx
            import hashlib
            import hmac
            from datetime import datetime

            date = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
            object_path = f"warehouse/items/{filename}"
            url = f"https://{self.bucket}.{self.endpoint}/{object_path}"

            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.put(
                    url,
                    content=file_data,
                    headers={
                        "Date": date,
                        "Content-Type": "application/octet-stream",
                    },
                )
                if resp.status_code == 200:
                    return url
                else:
                    logger.error(f"OSS 上传失败: {resp.status_code}")
                    return None
        except Exception as e:
            logger.error(f"OSS 上传异常: {e}")
            return None

    async def delete_image(self, url: str) -> bool:
        if not self._configured:
            return True
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.delete(url)
                return resp.status_code in (200, 204)
        except Exception as e:
            logger.error(f"OSS 删除异常: {e}")
            return False
