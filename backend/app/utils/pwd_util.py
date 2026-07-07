"""
密码加密工具模块
使用 bcrypt 加盐哈希，确保密码安全存储
所有注册、登录、修改密码接口统一调用此模块
"""

import bcrypt


def hash_password(plain_password):
    """对明文密码进行 bcrypt 加盐加密

    Args:
        plain_password: 用户输入的明文密码

    Returns:
        str: 加密后的密码哈希字符串
    """
    hashed = bcrypt.hashpw(plain_password.encode('utf-8'), bcrypt.gensalt())
    return hashed.decode('utf-8')


def check_password(plain_password, hashed_password):
    """验证明文密码是否与哈希值匹配

    Args:
        plain_password: 用户输入的明文密码
        hashed_password: 数据库中存储的哈希密码

    Returns:
        bool: 密码匹配返回 True，否则返回 False
    """
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )
