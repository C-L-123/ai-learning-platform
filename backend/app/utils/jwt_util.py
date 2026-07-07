"""
JWT 鉴权工具模块
提供 token 生成和 login_required 鉴权装饰器
所有需要登录的接口（OCR、刷题、错题等）统一使用 @login_required
"""

import jwt
import datetime
from functools import wraps
from flask import request, current_app

from app.utils.response_util import fail
from config import Config


def generate_token(user_id, username):
    """生成 JWT 令牌

    Args:
        user_id: 用户 ID
        username: 用户名

    Returns:
        str: JWT token 字符串
    """
    payload = {
        'user_id': user_id,
        'username': username,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=Config.JWT_EXPIRATION_DAYS),
        'iat': datetime.datetime.utcnow()
    }
    token = jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm='HS256')
    return token


def login_required(f):
    """登录鉴权装饰器

    从请求头 Authorization: Bearer <token> 中解析 JWT，
    验证通过后将当前用户信息以 current_user 字典形式传入视图函数。

    使用方式：
        @bp.route('/xxx')
        @login_required
        def my_view(current_user):
            user_id = current_user['user_id']
            ...
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # 从 Authorization 请求头提取 token
        if Config.JWT_HEADER_NAME in request.headers:
            auth_header = request.headers[Config.JWT_HEADER_NAME]
            if auth_header.startswith(Config.JWT_HEADER_PREFIX):
                token = auth_header[len(Config.JWT_HEADER_PREFIX):]

        if not token:
            return fail(message='Token 缺失，请先登录', code=401)

        try:
            data = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
            current_user = {
                'user_id': data['user_id'],
                'username': data['username']
            }
        except jwt.ExpiredSignatureError:
            return fail(message='Token 已过期，请重新登录', code=401)
        except jwt.InvalidTokenError:
            return fail(message='Token 无效，请重新登录', code=401)

        return f(current_user, *args, **kwargs)

    return decorated
