import json
from datetime import datetime, timedelta
from flask import Blueprint, request
from sqlalchemy import func

from app.models import db, WrongQuestion, Question, StudyRecord
from app.utils.jwt_util import login_required
from app.utils.response_util import success, fail

bp = Blueprint('wrong_question', __name__)


@bp.route('/list', methods=['GET'])
@login_required
def get_wrong_questions(current_user):
    """获取错题列表"""
    status = request.args.get('status', 'pending')  # pending:待复习, mastered:已掌握, all:全部
    subject = request.args.get('subject')
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)

    query = WrongQuestion.query.filter_by(user_id=current_user['user_id'])

    if status != 'all':
        query = query.filter_by(status=status)

    if subject:
        query = query.join(Question).filter(Question.subject == subject)

    total = query.count()
    wrong_questions = query.order_by(WrongQuestion.updated_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    result = []
    for wq in wrong_questions:
        q = wq.question
        result.append({
            'id': wq.id,
            'question_id': q.id,
            'subject': q.subject,
            'knowledge_point': q.knowledge_point,
            'difficulty': q.difficulty,
            'content': q.content,
            'options': json.loads(q.options) if q.options else None,
            'correct_answer': q.answer,
            'wrong_answer': wq.wrong_answer,
            'wrong_count': wq.wrong_count,
            'status': wq.status,
            'created_at': wq.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'last_review_at': wq.last_review_at.strftime('%Y-%m-%d %H:%M:%S') if wq.last_review_at else None
        })

    return success(data={
        'list': result,
        'total': total,
        'page': page,
        'page_size': page_size
    })


@bp.route('/review/<int:wrong_id>', methods=['POST'])
@login_required
def review_wrong_question(current_user, wrong_id):
    """复习错题并提交结果"""
    data = request.get_json()
    user_answer = data.get('answer')
    is_correct = data.get('is_correct', False)

    wrong_question = WrongQuestion.query.filter_by(id=wrong_id, user_id=current_user['user_id']).first()

    if not wrong_question:
        return fail(message='错题记录不存在', code=404)

    # 如果前端传了答案，后端再验证一次
    if user_answer is not None and wrong_question.question:
        is_correct = str(user_answer).strip() == str(wrong_question.question.answer).strip()

    # 更新复习时间
    wrong_question.last_review_at = datetime.now()

    if is_correct:
        # 答对了，减少错误计数；当错误计数归零则标记为已掌握
        if wrong_question.wrong_count <= 1:
            wrong_question.wrong_count = 0
            wrong_question.status = 'mastered'
        else:
            wrong_question.wrong_count -= 1
    else:
        # 答错了，错误次数+1，重置进度
        wrong_question.wrong_count += 1
        wrong_question.status = 'pending'
        wrong_question.wrong_answer = str(user_answer) if user_answer else wrong_question.wrong_answer

    # 记录学习记录
    study_record = StudyRecord(
        user_id=current_user['user_id'],
        question_id=wrong_question.question_id,
        study_type='review',
        is_correct=is_correct
    )
    db.session.add(study_record)

    # 同步更新知识点掌握度
    if wrong_question.question:
        from app.models import UserKnowledgeMastery
        mastery = UserKnowledgeMastery.query.filter_by(
            user_id=current_user['user_id'],
            knowledge_point=wrong_question.question.knowledge_point
        ).first()
        if mastery:
            if is_correct:
                mastery.mastery_rate = min(100, mastery.mastery_rate + 5)
            else:
                mastery.mastery_rate = max(0, mastery.mastery_rate - 10)

    db.session.commit()

    return success(data={
        'is_correct': is_correct,
        'new_status': wrong_question.status,
        'remaining_wrong_count': wrong_question.wrong_count
    }, message='提交成功')


@bp.route('/mark-mastered/<int:wrong_id>', methods=['POST'])
@login_required
def mark_as_mastered(current_user, wrong_id):
    """标记为已掌握"""
    wrong_question = WrongQuestion.query.filter_by(id=wrong_id, user_id=current_user['user_id']).first()

    if not wrong_question:
        return fail(message='错题记录不存在', code=404)

    wrong_question.status = 'mastered'
    db.session.commit()

    return success(message='标记成功')


@bp.route('/remove/<int:wrong_id>', methods=['DELETE'])
@login_required
def remove_wrong_question(current_user, wrong_id):
    """从错题本移除"""
    wrong_question = WrongQuestion.query.filter_by(id=wrong_id, user_id=current_user['user_id']).first()

    if not wrong_question:
        return fail(message='错题记录不存在', code=404)

    db.session.delete(wrong_question)
    db.session.commit()

    return success(message='移除成功')


@bp.route('/statistics', methods=['GET'])
@login_required
def get_wrong_statistics(current_user):
    """获取错题统计"""
    total_wrong = WrongQuestion.query.filter_by(user_id=current_user['user_id']).count()
    pending_count = WrongQuestion.query.filter_by(user_id=current_user['user_id'], status='pending').count()
    mastered_count = WrongQuestion.query.filter_by(user_id=current_user['user_id'], status='mastered').count()

    # 按科目统计
    subject_stats = db.session.query(
        Question.subject,
        func.count(WrongQuestion.id)
    ).join(Question).filter(
        WrongQuestion.user_id == current_user['user_id']
    ).group_by(Question.subject).all()

    subject_distribution = []
    for subject, count in subject_stats:
        subject_distribution.append({
            'subject': subject,
            'count': count
        })

    return success(data={
        'total_wrong': total_wrong,
        'pending_count': pending_count,
        'mastered_count': mastered_count,
        'subject_distribution': subject_distribution
    })


@bp.route('/review-today', methods=['GET'])
@login_required
def get_today_review(current_user):
    """获取今日待复习的错题"""
    today = datetime.now().date()

    # 获取需要复习的错题（上次复习超过1天或从未复习）
    review_questions = WrongQuestion.query.filter_by(
        user_id=current_user['user_id'],
        status='pending'
    ).filter(
        (WrongQuestion.last_review_at == None) |
        (func.date(WrongQuestion.last_review_at) < today)
    ).order_by(WrongQuestion.wrong_count.desc()).limit(20).all()

    result = []
    for wq in review_questions:
        q = wq.question
        result.append({
            'id': wq.id,
            'question_id': q.id,
            'content': q.content,
            'knowledge_point': q.knowledge_point,
            'wrong_count': wq.wrong_count,
            'options': json.loads(q.options) if q.options else None,
            'correct_answer': q.answer,
            'analysis': q.analysis or '',
            'question_type': q.question_type or '单选'
        })

    return success(data={
        'count': len(result),
        'questions': result
    })
