"""
刷题练习蓝图
所有 AI 出题、判分、统计逻辑已移入 services/
本文件只保留路由：接参数 → 调服务 → 返结果
"""

import os
import uuid
from flask import Blueprint, request, current_app
from werkzeug.utils import secure_filename

from app.models import db, Question, StudyRecord, WrongQuestion, UserKnowledgeMastery
from app.utils.jwt_util import login_required
from app.utils.response_util import success, fail
from app.utils.file_util import validate_image_file, get_file_extension
from app.services.llm_service import LLMService
from app.services.stat_service import StatService

bp = Blueprint('practice', __name__)


# ==================== AI 出题 ====================

@bp.route('/questions', methods=['GET'])
@login_required
def get_questions(current_user):
    """AI 生成题目列表"""
    subject = request.args.get('subject', '数学')
    knowledge_point = request.args.get('knowledge_point')
    difficulty = request.args.get('difficulty', 0, type=int)
    count = min(request.args.get('page_size', 10, type=int), 20)
    question_type = request.args.get('question_type')

    questions_data = LLMService.generate_questions(
        subject=subject,
        knowledge_point=knowledge_point,
        difficulty=difficulty,
        count=count,
        question_type=question_type,
    )

    if not questions_data:
        return fail(message='AI 出题失败，请稍后重试', code=500)

    saved = _save_questions(questions_data, subject)

    return success(data={
        'list': saved,
        'total': len(saved),
        'page': 1,
        'page_size': count,
    }, message='出题成功')


@bp.route('/smart-recommend', methods=['GET'])
@login_required
def smart_recommend(current_user):
    """智能推荐题目 — AI 根据薄弱知识点出题"""
    subject = request.args.get('subject', '数学')
    count = min(request.args.get('count', 10, type=int), 20)

    weak_points = UserKnowledgeMastery.query.filter_by(
        user_id=current_user['user_id'], subject=subject
    ).filter(
        UserKnowledgeMastery.mastery_rate < 75
    ).order_by(UserKnowledgeMastery.mastery_rate).all()

    weak_point_names = [wp.knowledge_point for wp in weak_points[:5]] if weak_points else []
    kp_hint = '、'.join(weak_point_names) if weak_point_names else None

    questions_data = LLMService.generate_questions(
        subject=subject,
        knowledge_point=kp_hint,
        difficulty=2,
        count=count,
    )

    if not questions_data:
        return fail(message='AI 出题失败，请稍后重试', code=500)

    saved = _save_questions(questions_data, subject)

    return success(data={
        'questions': saved,
        'weak_points_focused': weak_point_names,
    }, message='推荐成功')


# ==================== 答题 ====================

@bp.route('/submit-answer', methods=['POST'])
@login_required
def submit_answer(current_user):
    """提交答案并判分"""
    data = request.get_json()
    question_id = data.get('question_id')
    user_answer = data.get('answer')
    answer_time = data.get('answer_time', 0)
    image_path = data.get('image_path')

    if not question_id or user_answer is None:
        return fail(message='参数不完整', code=400)

    question = Question.query.get(question_id)
    if not question:
        return fail(message='题目不存在', code=404)

    score = None
    feedback = None

    # 判分
    if question.question_type == '解答':
        grade_result = LLMService.grade_essay(
            question.content, question.answer, user_answer, image_path
        )
        is_correct = grade_result['is_correct']
        score = grade_result['score']
        feedback = grade_result['feedback']
    else:
        is_correct = str(user_answer).strip() == str(question.answer).strip()

    # 记录学习记录
    study_record = StudyRecord(
        user_id=current_user['user_id'],
        question_id=question_id,
        study_type='practice',
        is_correct=is_correct,
        answer_time=answer_time,
    )
    db.session.add(study_record)

    # 更新知识点掌握度
    mastery = UserKnowledgeMastery.query.filter_by(
        user_id=current_user['user_id'],
        knowledge_point=question.knowledge_point,
    ).first()

    if mastery:
        mastery.total_questions += 1
        if is_correct:
            mastery.correct_questions += 1
            mastery.mastery_rate = min(100, mastery.mastery_rate + 5)
        else:
            mastery.mastery_rate = max(0, mastery.mastery_rate - 10)
    else:
        new_mastery = UserKnowledgeMastery(
            user_id=current_user['user_id'],
            knowledge_point=question.knowledge_point,
            subject=question.subject,
            total_questions=1,
            correct_questions=1 if is_correct else 0,
            mastery_rate=55 if is_correct else 40,
        )
        db.session.add(new_mastery)

    # 答错加入错题本
    if not is_correct:
        existing_wrong = WrongQuestion.query.filter_by(
            user_id=current_user['user_id'],
            question_id=question_id,
        ).first()

        if existing_wrong:
            existing_wrong.wrong_count += 1
            existing_wrong.status = 'pending'
        else:
            wrong_question = WrongQuestion(
                user_id=current_user['user_id'],
                question_id=question_id,
                wrong_answer=str(user_answer),
                status='pending',
            )
            db.session.add(wrong_question)

    db.session.commit()

    result_data = {
        'is_correct': is_correct,
        'correct_answer': question.answer,
        'analysis': question.analysis,
        'knowledge_point': question.knowledge_point,
        'question_type': question.question_type,
    }
    if score is not None:
        result_data['score'] = score
        result_data['feedback'] = feedback

    return success(data=result_data, message='提交成功')


# ==================== 统计 ====================

@bp.route('/statistics', methods=['GET'])
@login_required
def get_practice_statistics(current_user):
    """获取刷题统计数据"""
    data = StatService.get_practice_stats(current_user['user_id'])
    return success(data=data)


@bp.route('/session-complete', methods=['POST'])
@login_required
def session_complete(current_user):
    """记录一次刷题会话的总时长"""
    data = request.get_json()
    total_time = data.get('total_time', 0)

    if total_time > 0:
        record = StudyRecord(
            user_id=current_user['user_id'],
            question_id=None,
            study_type='practice_session',
            is_correct=None,
            answer_time=total_time,
        )
        db.session.add(record)
        db.session.commit()

    return success(data={'total_time': total_time}, message='记录成功')


@bp.route('/daily-trend', methods=['GET'])
@login_required
def get_daily_trend(current_user):
    """获取每日刷题趋势（最近7天）"""
    data = StatService.get_daily_trend(current_user['user_id'])
    return success(data=data)


# ==================== 图片上传 ====================

@bp.route('/upload-image', methods=['POST'])
@login_required
def upload_answer_image(current_user):
    """上传解答题的作答图片"""
    file = request.files.get('file')
    is_valid, error_msg = validate_image_file(file)
    if not is_valid:
        return fail(message=error_msg, code=400)

    ext = get_file_extension(file.filename)
    filename = secure_filename(f"practice_{uuid.uuid4().hex}_{file.filename}")
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)

    return success(data={'image_path': filepath}, message='上传成功')


# ==================== 内部辅助 ====================

def _save_questions(questions_data, subject):
    """将 AI 生成的题目存入数据库并返回格式化列表"""
    import json
    saved = []
    for qd in questions_data:
        question = Question(
            subject=subject,
            knowledge_point=qd.get('knowledge_point', '综合'),
            difficulty=qd.get('difficulty', 1),
            question_type=qd.get('question_type', '单选'),
            content=qd['content'],
            options=json.dumps(qd.get('options', []), ensure_ascii=False),
            answer=qd['answer'],
            analysis=qd.get('analysis', ''),
        )
        db.session.add(question)
        db.session.flush()
        saved.append({
            'id': question.id,
            'subject': question.subject,
            'knowledge_point': question.knowledge_point,
            'difficulty': question.difficulty,
            'question_type': question.question_type,
            'content': question.content,
            'options': json.loads(question.options) if question.options else None,
            'answer': question.answer,
            'analysis': question.analysis or '',
        })
    db.session.commit()
    return saved
