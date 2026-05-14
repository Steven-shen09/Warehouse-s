"""安全工具：密码哈希、JWT 生成与验证"""
import hashlib
import os
from datetime import datetime, timedelta
from jose import jwt, JWTError
from app.config import settings


def hash_password(password: str) -> str:
    """使用 PBKDF2-SHA256 对密码进行哈希"""
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000, dklen=64)
    # 存储格式：salt_hex$key_hex
    return salt.hex() + "$" + key.hex()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证明文密码与哈希是否匹配"""
    try:
        salt_hex, key_hex = hashed_password.split("$", 1)
        salt = bytes.fromhex(salt_hex)
        stored_key = bytes.fromhex(key_hex)
        computed_key = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, 100000, dklen=64)
        return computed_key == stored_key
    except Exception:
        return False


def create_access_token(user_id: int, username: str, role: str) -> str:
    """生成 JWT 访问令牌"""
    expire = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRE_HOURS)
    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "exp": expire,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def verify_token(token: str) -> dict:
    """验证 JWT 令牌，返回载荷；验证失败抛出 JWTError"""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
