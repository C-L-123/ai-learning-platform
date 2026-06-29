import json
from flask import Blueprint, request, jsonify

from app.models import db, Subject
from app.utils.jwt_auth import token_required

bp = Blueprint('subject', __name__)


@bp.route('/list', methods=['GET'])
def get_subjects():
    """获取所有启用的科目列表（无需登录）"""
    subjects = Subject.query.filter_by(is_active=True).order_by(Subject.id).all()

    result = []
    for s in subjects:
        result.append({
            'id': s.id,
            'name': s.name,
            'keywords': json.loads(s.keywords) if s.keywords else [],
            'description': s.description
        })

    return jsonify({
        'code': 200,
        'message': '获取成功',
        'data': result
    })


@bp.route('/all', methods=['GET'])
@token_required
def get_all_subjects(current_user):
    """获取所有科目列表（含禁用，管理用）"""
    subjects = Subject.query.order_by(Subject.id).all()

    result = []
    for s in subjects:
        result.append({
            'id': s.id,
            'name': s.name,
            'keywords': json.loads(s.keywords) if s.keywords else [],
            'description': s.description,
            'is_active': s.is_active,
            'created_at': s.created_at.strftime('%Y-%m-%d %H:%M:%S') if s.created_at else None
        })

    return jsonify({
        'code': 200,
        'message': '获取成功',
        'data': result
    })


@bp.route('/add', methods=['POST'])
@token_required
def add_subject(current_user):
    """新增科目"""
    data = request.get_json()

    name = data.get('name', '').strip()
    if not name:
        return jsonify({'code': 400, 'message': '科目名称不能为空', 'data': None}), 400

    # 检查是否重名
    if Subject.query.filter_by(name=name).first():
        return jsonify({'code': 400, 'message': '科目名称已存在', 'data': None}), 400

    keywords = data.get('keywords', [])
    if isinstance(keywords, str):
        # 支持逗号分隔的字符串输入
        keywords = [k.strip() for k in keywords.split(',') if k.strip()]

    subject = Subject(
        name=name,
        keywords=json.dumps(keywords, ensure_ascii=False),
        description=data.get('description', ''),
        is_active=True
    )

    db.session.add(subject)
    db.session.commit()

    return jsonify({
        'code': 200,
        'message': '添加成功',
        'data': {
            'id': subject.id,
            'name': subject.name,
            'keywords': keywords,
            'description': subject.description
        }
    })


@bp.route('/update/<int:subject_id>', methods=['POST'])
@token_required
def update_subject(current_user, subject_id):
    """更新科目"""
    subject = Subject.query.get(subject_id)
    if not subject:
        return jsonify({'code': 404, 'message': '科目不存在', 'data': None}), 404

    data = request.get_json()

    if 'name' in data:
        new_name = data['name'].strip()
        if not new_name:
            return jsonify({'code': 400, 'message': '科目名称不能为空', 'data': None}), 400
        existing = Subject.query.filter(Subject.name == new_name, Subject.id != subject_id).first()
        if existing:
            return jsonify({'code': 400, 'message': '科目名称已存在', 'data': None}), 400
        subject.name = new_name

    if 'keywords' in data:
        keywords = data['keywords']
        if isinstance(keywords, str):
            keywords = [k.strip() for k in keywords.split(',') if k.strip()]
        subject.keywords = json.dumps(keywords, ensure_ascii=False)

    if 'description' in data:
        subject.description = data['description']

    if 'is_active' in data:
        subject.is_active = data['is_active']

    db.session.commit()

    return jsonify({
        'code': 200,
        'message': '更新成功',
        'data': None
    })


@bp.route('/delete/<int:subject_id>', methods=['DELETE'])
@token_required
def delete_subject(current_user, subject_id):
    """删除科目"""
    subject = Subject.query.get(subject_id)
    if not subject:
        return jsonify({'code': 404, 'message': '科目不存在', 'data': None}), 404

    db.session.delete(subject)
    db.session.commit()

    return jsonify({
        'code': 200,
        'message': '删除成功',
        'data': None
    })
