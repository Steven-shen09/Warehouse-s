"""全局配置管理"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置，自动从 .env 文件读取"""

    # 应用基础
    SECRET_KEY: str = "change-me-in-production"
    DATABASE_PATH: str = "data/warehouse.db"
    APPROVAL_TIMEOUT_HOURS: int = 24

    # DeepSeek AI（审核建议、异常检测）
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"

    # Moonshot Kimi AI（前端页面生成、图像生成）
    KIMI_API_KEY: str = ""
    KIMI_BASE_URL: str = "https://api.moonshot.cn/v1"

    # 阿里云 OSS
    OSS_ACCESS_KEY_ID: str = ""
    OSS_ACCESS_KEY_SECRET: str = ""
    OSS_BUCKET_NAME: str = ""
    OSS_ENDPOINT: str = ""

    # 阿里云 SMS
    SMS_ACCESS_KEY_ID: str = ""
    SMS_ACCESS_KEY_SECRET: str = ""
    SMS_SIGN_NAME: str = ""
    SMS_TEMPLATE_CODE: str = ""

    # JWT 配置
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 24

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
