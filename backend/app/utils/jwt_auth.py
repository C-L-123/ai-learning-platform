import jwt
import datetime
from functools import wraps
from flask import request, jsonify, current_app

def generate_token(user_id, username):
    """生成JWT令牌"""
    payload = {
        'user_id': user_id,
        'username': username,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7),
        'iat': datetime.datetime.utcnow()
    }
    token = jwt.encode(payload, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')
    return token

def token_required(f):
    """JWT认证装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]
        
        if not token:
            return jsonify({'code': 401, 'message': 'Token缺失', 'data': None}), 401
        
        try:
            data = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
            current_user = {
                'user_id': data['user_id'],
                'username': data['username']
            }
        except jwt.ExpiredSignatureError:
            return jsonify({'code': 401, 'message': 'Token已过期', 'data': None}), 401
        except jwt.InvalidTokenError:
            return jsonify({'code': 401, 'message': 'Token无效', 'data': None}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated
