import os
import json
import uuid
from datetime import datetime, date
from flask import Blueprint, request, jsonify, current_app
from sqlalchemy import func
from werkzeug.utils import secure_filename

from app.models import db, Question, StudyRecord, WrongQuestion, UserKnowledgeMastery
from app.utils.jwt_auth import token_required

bp = Blueprint('practice', __name__)

_ai_service = None

def get_ai_service():
    global _ai_service
    if _ai_service is None:
        from app.utils.ai_question_service import AIQuestionService
        _ai_service = AIQuestionService()
    return _ai_service


def _save_questions_to_db(questions_data, subject):
    """将 AI 生成的题目存入数据库并返回 Question 对象列表"""
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
            analysis=qd.get('analysis', '')
        )
        db.session.add(question)
        db.session.flush()  # 获取 id
        saved.append(question)
    db.session.commit()
    return saved


def _format_question(q):
    """格式化题目为返回字典"""
    return {
        'id': q.id,
        'subject': q.subject,
        'knowledge_point': q.knowledge_point,
        'difficulty': q.difficulty,
        'question_type': q.question_type,
        'content': q.content,
        'options': json.loads(q.options) if q.options else None,
        'answer': q.answer,
        'analysis': q.analysis or ''
    }


@bp.route('/questions', methods=['GET'])
@token_required
def get_questions(current_user):
    """AI 生成题目列表"""
    subject = request.args.get('subject', '数学')
    knowledge_point = request.args.get('knowledge_point')
    difficulty = request.args.get('difficulty', 0, type=int)
    count = request.args.get('page_size', 10, type=int)
    question_type = request.args.get('question_type')

    # 限制单次出题数量
    count = min(count, 20)

    try:
        ai = get_ai_service()
        questions_data = ai.generate_questions(
            subject=subject,
            knowledge_point=knowledge_point,
            difficulty=difficulty,
            count=count,
            question_type=question_type
        )

        if not questions_data:
            return jsonify({'code': 500, 'message': 'AI 出题失败，请稍后重试', 'data': None}), 500

        saved = _save_questions_to_db(questions_data, subject)
        result = [_format_question(q) for q in saved]

        return jsonify({
            'code': 200,
            'message': '出题成功',
            'data': {
                'list': result,
                'total': len(result),
                'page': 1,
                'page_size': count
            }
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': f'AI 出题异常: {str(e)}', 'data': None}), 500

@bp.route('/smart-recommend', methods=['GET'])
@token_required
def smart_recommend(current_user):
    """智能推荐题目 — AI 根据薄弱知识点出题"""
    subject = request.args.get('subject', '数学')
    count = request.args.get('count', 10, type=int)
    count = min(count, 20)

    # 获取用户薄弱知识点
    weak_points = UserKnowledgeMastery.query.filter_by(
        user_id=current_user['user_id'],
        subject=subject
    ).filter(UserKnowledgeMastery.mastery_rate < 75).order_by(UserKnowledgeMastery.mastery_rate).all()

    weak_point_names = [wp.knowledge_point for wp in weak_points[:5]] if weak_points else []

    # 构建针对薄弱知识点的出题提示
    kp_hint = '、'.join(weak_point_names) if weak_point_names else None

    try:
        ai = get_ai_service()
        questions_data = ai.generate_questions(
            subject=subject,
            knowledge_point=kp_hint,
            difficulty=2,
            count=count
        )

        if not questions_data:
            return jsonify({'code': 500, 'message': 'AI 出题失败，请稍后重试', 'data': None}), 500

        saved = _save_questions_to_db(questions_data, subject)
        result = [_format_question(q) for q in saved]

        return jsonify({
            'code': 200,
            'message': '推荐成功',
            'data': {
                'questions': result,
                'weak_points_focused': weak_point_names
            }
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': f'AI 出题异常: {str(e)}', 'data': None}), 500

@bp.route('/submit-answer', methods=['POST'])
@token_required
def submit_answer(current_user):
    """提交答案并判分"""
    data = request.get_json()
    question_id = data.get('question_id')
    user_answer = data.get('answer')
    answer_time = data.get('answer_time', 0)
    image_path = data.get('image_path')
    
    if not question_id or user_answer is None:
        return jsonify({'code': 400, 'message': '参数不完整', 'data': None}), 400

    question = Question.query.get(question_id)
    if not question:
        return jsonify({'code': 404, 'message': '题目不存在', 'data': None}), 404

    score = None
    feedback = None

    # 判断答案是否正确
    if question.question_type == '解答':
        # 解答题：调用 AI 判分
        ai = get_ai_service()
        grade_result = ai.grade_essay(question.content, question.answer, user_answer, image_path)
        is_correct = grade_result['is_correct']
        score = grade_result['score']
        feedback = grade_result['feedback']
    else:
        # 选择题：字符串比较
        is_correct = str(user_answer).strip() == str(question.answer).strip()
    
    # 记录学习记录
    study_record = StudyRecord(
        user_id=current_user['user_id'],
        question_id=question_id,
        study_type='practice',
        is_correct=is_correct,
        answer_time=answer_time
    )
    db.session.add(study_record)
    
    # 更新知识点掌握度（答对+5%，答错-10%，范围0-100）
    mastery = UserKnowledgeMastery.query.filter_by(
        user_id=current_user['user_id'],
        knowledge_point=question.knowledge_point
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
            mastery_rate=55 if is_correct else 40
        )
        db.session.add(new_mastery)
    
    # 如果答错，加入错题本
    if not is_correct:
        existing_wrong = WrongQuestion.query.filter_by(
            user_id=current_user['user_id'],
            question_id=question_id
        ).first()
        
        if existing_wrong:
            existing_wrong.wrong_count += 1
            existing_wrong.status = 'pending'
        else:
            wrong_question = WrongQuestion(
                user_id=current_user['user_id'],
                question_id=question_id,
                wrong_answer=str(user_answer),
                status='pending'
            )
            db.session.add(wrong_question)
    
    db.session.commit()
    
    result_data = {
        'is_correct': is_correct,
        'correct_answer': question.answer,
        'analysis': question.analysis,
        'knowledge_point': question.knowledge_point,
        'question_type': question.question_type
    }
    if score is not None:
        result_data['score'] = score
        result_data['feedback'] = feedback

    return jsonify({
        'code': 200,
        'message': '提交成功',
        'data': result_data
    })

@bp.route('/statistics', methods=['GET'])
@token_required
def get_practice_statistics(current_user):
    """获取刷题统计数据"""
    today = date.today()
    
    # 总刷题数
    total_practice = StudyRecord.query.filter_by(
        user_id=current_user['user_id'],
        study_type='practice'
    ).count()
    
    # 正确数
    correct_count = StudyRecord.query.filter_by(
        user_id=current_user['user_id'],
        study_type='practice',
        is_correct=True
    ).count()
    
    # 今日刷题数
    today_count = StudyRecord.query.filter_by(
        user_id=current_user['user_id'],
        study_type='practice'
    ).filter(func.date(StudyRecord.created_at) == today).count()
    
    # 总学习时长（秒）- 从整场学习记录中取
    total_time = db.session.query(func.sum(StudyRecord.answer_time)).filter_by(
        user_id=current_user['user_id'],
        study_type='practice_session'
    ).scalar() or 0
    
    accuracy = (correct_count / total_practice * 100) if total_practice > 0 else 0
    
    return jsonify({
        'code': 200,
        'message': '获取成功',
        'data': {
            'total_practice': total_practice,
            'correct_count': correct_count,
            'accuracy': round(accuracy, 1),
            'today_count': today_count,
            'total_study_time': total_time
        }
    })

@bp.route('/session-complete', methods=['POST'])
@token_required
def session_complete(current_user):
    """记录一次刷题会话的总时长"""
    data = request.get_json()
    total_time = data.get('total_time', 0)
    question_count = data.get('question_count', 0)

    if total_time > 0:
        record = StudyRecord(
            user_id=current_user['user_id'],
            question_id=None,
            study_type='practice_session',
            is_correct=None,
            answer_time=total_time
        )
        db.session.add(record)
        db.session.commit()

    return jsonify({
        'code': 200,
        'message': '记录成功',
        'data': {'total_time': total_time}
    })


@bp.route('/daily-trend', methods=['GET'])
@token_required
def get_daily_trend(current_user):
    """获取每日刷题趋势（最近7天）"""
    days = 7
    trend_data = []
    
    for i in range(days - 1, -1, -1):
        day = date.fromordinal(date.today().toordinal() - i)
        day_str = day.strftime('%m-%d')
        
        day_count = StudyRecord.query.filter_by(
            user_id=current_user['user_id'],
            study_type='practice'
        ).filter(func.date(StudyRecord.created_at) == day).count()
        
        day_correct = StudyRecord.query.filter_by(
            user_id=current_user['user_id'],
            study_type='practice',
            is_correct=True
        ).filter(func.date(StudyRecord.created_at) == day).count()
        
        accuracy = (day_correct / day_count * 100) if day_count > 0 else 0
        
        trend_data.append({
            'date': day_str,
            'count': day_count,
            'accuracy': round(accuracy, 1)
        })
    
    return jsonify({
        'code': 200,
        'message': '获取成功',
        'data': trend_data
    })


@bp.route('/upload-image', methods=['POST'])
@token_required
def upload_answer_image(current_user):
    """上传解答题的作答图片"""
    if 'file' not in request.files:
        return jsonify({'code': 400, 'message': '没有上传文件', 'data': None}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'code': 400, 'message': '没有选择文件', 'data': None}), 400

    allowed = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}
    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    if ext not in allowed:
        return jsonify({'code': 400, 'message': '不支持的文件格式', 'data': None}), 400

    filename = secure_filename(f"practice_{uuid.uuid4().hex}_{file.filename}")
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)

    return jsonify({
        'code': 200,
        'message': '上传成功',
        'data': {'image_path': filepath}
    })
