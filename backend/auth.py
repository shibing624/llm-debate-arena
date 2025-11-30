# -*- coding: utf-8 -*-
"""
@author:XuMing(xuming624@qq.com)
@description: 用户认证模块
"""

import hashlib
import jwt
from datetime import datetime, timedelta
from typing import Optional

SECRET_KEY = "your-secret-key-change-in-production"  # 生产环境需要修改
ALGORITHM = "HS256"
# Token 永久有效（不设置过期时间）


def hash_password(password: str) -> str:
    """密码哈希"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return hash_password(plain_password) == hashed_password


def create_access_token(data: dict) -> str:
    """创建JWT token（永久有效）"""
    to_encode = data.copy()
    # 不设置 exp 字段，token 永久有效
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """解码JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None
