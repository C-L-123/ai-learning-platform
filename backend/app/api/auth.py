from flask import Blueprint, request

from app.models import db, User
from app.utils.pwd_util import hash_password, check_password
from app.utils.response_util import success, fail
from app.utils.jwt_util import generate_token, login_required
from app.utils.logger_util import log_login_action

bp = Blueprint('auth', __name__)


@bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.get_json()

    if not data or not data.get('username') or not data.get('password') or not data.get('email'):
        return fail(message='用户名、密码和邮箱不能为空', code=400)

    # 检查用户名是否已存在
    if User.query.filter_by(username=data['username']).first():
        return fail(message='用户名已存在', code=400)

    # 检查邮箱是否已存在
    if User.query.filter_by(email=data['email']).first():
        return fail(message='邮箱已被注册', code=400)

    # 加密密码（bcrypt 加盐）
    hashed_password = hash_password(data['password'])

    # 创建用户
    user = User(
        username=data['username'],
        email=data['email'],
        password=hashed_password,
        nickname=data.get('nickname', data['username'])
    )

    db.session.add(user)
    db.session.commit()

    log_login_action(
        data['username'], 'register',
        ip=request.remote_addr, user_id=user.id
    )

    return success(data={
        'user_id': user.id,
        'username': user.username,
        'email': user.email
    }, message='注册成功')


@bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json()

    if not data or not data.get('username') or not data.get('password'):
        return fail(message='用户名和密码不能为空', code=400)

    user = User.query.filter_by(username=data['username']).first()

    if not user:
        log_login_action(data['username'], 'fail', ip=request.remote_addr, error='用户不存在')
        return fail(message='用户不存在', code=400)

    # 验证密码（bcrypt 校验）
    if not check_password(data['password'], user.password):
        log_login_action(data['username'], 'fail', ip=request.remote_addr, error='密码错误')
        return fail(message='密码错误', code=400)

    # 生成 token
    token = generate_token(user.id, user.username)

    log_login_action(data['username'], 'success', ip=request.remote_addr, user_id=user.id)

    return success(data={
        'token': token,
        'user_info': {
            'user_id': user.id,
            'username': user.username,
            'nickname': user.nickname,
            'email': user.email,
            'avatar': user.avatar
        }
    }, message='登录成功')


@bp.route('/user-info', methods=['GET'])
@login_required
def get_user_info(current_user):
    """获取用户信息"""
    user = User.query.get(current_user['user_id'])

    return success(data={
        'user_id': user.id,
        'username': user.username,
        'nickname': user.nickname,
        'email': user.email,
        'avatar': user.avatar,
        'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S')
    }, message='获取成功')


@bp.route('/update-profile', methods=['POST'])
@login_required
def update_profile(current_user):
    """更新用户信息"""
    data = request.get_json()
    user = User.query.get(current_user['user_id'])

    if data.get('nickname'):
        user.nickname = data['nickname']
    if data.get('avatar'):
        user.avatar = data['avatar']

    db.session.commit()

    return success(message='更新成功')


@bp.route('/change-password', methods=['POST'])
@login_required
def change_password(current_user):
    """修改密码"""
    data = request.get_json()
    user = User.query.get(current_user['user_id'])

    if not data.get('old_password') or not data.get('new_password'):
        return fail(message='旧密码和新密码不能为空', code=400)

    # 验证旧密码
    if not check_password(data['old_password'], user.password):
        return fail(message='旧密码错误', code=400)

    # 更新密码（bcrypt 加盐）
    user.password = hash_password(data['new_password'])

    db.session.commit()

    return success(message='密码修改成功')
