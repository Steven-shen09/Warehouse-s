"""第三方服务适配器抽象基类"""
from abc import ABC, abstractmethod
from typing import Optional


class AIAdapter(ABC):
    """AI 服务适配器抽象基类"""

    @abstractmethod
    async def get_approval_suggestion(self, record_info: dict) -> Optional[str]:
        """获取智能审核建议，失败返回 None"""
        ...

    @abstractmethod
    async def detect_anomaly(self, records: list) -> list:
        """异常检测，返回异常记录列表"""
        ...


class OSSAdapter(ABC):
    """对象存储适配器抽象基类"""

    @abstractmethod
    async def upload_image(self, file_data: bytes, filename: str) -> Optional[str]:
        """上传图片，返回访问 URL"""
        ...

    @abstractmethod
    async def delete_image(self, url: str) -> bool:
        """删除图片"""
        ...


class SMSAdapter(ABC):
    """短信服务适配器抽象基类"""

    @abstractmethod
    async def send_notification(self, phone: str, template_code: str, params: dict) -> bool:
        """发送短信通知，返回是否成功"""
        ...
