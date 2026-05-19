from flask import Blueprint, request, jsonify
import bcrypt
from app.models import db, User
from app.utils.jwt_auth import generate_token, token_required

bp = Blueprint('auth', __name__)

@bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password') or not data.get('email'):
        return jsonify({'code': 400, 'message': '用户名、密码和邮箱不能为空', 'data': None}), 400
    
    # 检查用户名是否已存在
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'code': 400, 'message': '用户名已存在', 'data': None}), 400
    
    # 检查邮箱是否已存在
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'code': 400, 'message': '邮箱已被注册', 'data': None}), 400
    
    # 加密密码
    hashed_password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
    
    # 创建用户
    user = User(
        username=data['username'],
        email=data['email'],
        password=hashed_password.decode('utf-8'),
        nickname=data.get('nickname', data['username'])
    )
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': '注册成功',
        'data': {
            'user_id': user.id,
            'username': user.username,
            'email': user.email
        }
    })

@bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'code': 400, 'message': '用户名和密码不能为空', 'data': None}), 400
    
    user = User.query.filter_by(username=data['username']).first()
    
    if not user:
        return jsonify({'code': 400, 'message': '用户不存在', 'data': None}), 400
    
    # 验证密码
    if not bcrypt.checkpw(data['password'].encode('utf-8'), user.password.encode('utf-8')):
        return jsonify({'code': 400, 'message': '密码错误', 'data': None}), 400
    
    # 生成token
    token = generate_token(user.id, user.username)
    
    return jsonify({
        'code': 200,
        'message': '登录成功',
        'data': {
            'token': token,
            'user_info': {
                'user_id': user.id,
                'username': user.username,
                'nickname': user.nickname,
                'email': user.email,
                'avatar': user.avatar
            }
        }
    })

@bp.route('/user-info', methods=['GET'])
@token_required
def get_user_info(current_user):
    """获取用户信息"""
    user = User.query.get(current_user['user_id'])
    
    return jsonify({
        'code': 200,
        'message': '获取成功',
        'data': {
            'user_id': user.id,
            'username': user.username,
            'nickname': user.nickname,
            'email': user.email,
            'avatar': user.avatar,
            'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    })

@bp.route('/update-profile', methods=['POST'])
@token_required
def update_profile(current_user):
    """更新用户信息"""
    data = request.get_json()
    user = User.query.get(current_user['user_id'])
    
    if data.get('nickname'):
        user.nickname = data['nickname']
    if data.get('avatar'):
        user.avatar = data['avatar']
    
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': '更新成功',
        'data': None
    })

@bp.route('/change-password', methods=['POST'])
@token_required
def change_password(current_user):
    """修改密码"""
    data = request.get_json()
    user = User.query.get(current_user['user_id'])
    
    if not data.get('old_password') or not data.get('new_password'):
        return jsonify({'code': 400, 'message': '旧密码和新密码不能为空', 'data': None}), 400
    
    # 验证旧密码
    if not bcrypt.checkpw(data['old_password'].encode('utf-8'), user.password.encode('utf-8')):
        return jsonify({'code': 400, 'message': '旧密码错误', 'data': None}), 400
    
    # 更新密码
    hashed_password = bcrypt.hashpw(data['new_password'].encode('utf-8'), bcrypt.gensalt())
    user.password = hashed_password.decode('utf-8')
    
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': '密码修改成功',
        'data': None
    })
