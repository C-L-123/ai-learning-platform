import json
import random
from datetime import datetime, date
from flask import Blueprint, request, jsonify
from sqlalchemy import func

from app.models import db, Question, StudyRecord, WrongQuestion, UserKnowledgeMastery
from app.utils.jwt_auth import token_required

bp = Blueprint('practice', __name__)

@bp.route('/questions', methods=['GET'])
@token_required
def get_questions(current_user):
    """获取题目列表"""
    subject = request.args.get('subject', '数学')
    knowledge_point = request.args.get('knowledge_point')
    difficulty = request.args.get('difficulty', type=int)
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    
    query = Question.query.filter_by(subject=subject)
    
    if knowledge_point:
        query = query.filter(Question.knowledge_point == knowledge_point)
    if difficulty:
        query = query.filter(Question.difficulty == difficulty)
    
    total = query.count()
    questions = query.offset((page - 1) * page_size).limit(page_size).all()
    
    result = []
    for q in questions:
        result.append({
            'id': q.id,
            'subject': q.subject,
            'knowledge_point': q.knowledge_point,
            'difficulty': q.difficulty,
            'question_type': q.question_type,
            'content': q.content,
            'options': json.loads(q.options) if q.options else None
        })
    
    return jsonify({
        'code': 200,
        'message': '获取成功',
        'data': {
            'list': result,
            'total': total,
            'page': page,
            'page_size': page_size
        }
    })

@bp.route('/smart-recommend', methods=['GET'])
@token_required
def smart_recommend(current_user):
    """智能推荐题目（基于薄弱知识点）"""
    subject = request.args.get('subject', '数学')
    count = request.args.get('count', 10, type=int)
    
    # 获取用户薄弱知识点
    weak_points = UserKnowledgeMastery.query.filter_by(
        user_id=current_user['user_id'],
        subject=subject
    ).filter(UserKnowledgeMastery.mastery_rate < 75).order_by(UserKnowledgeMastery.mastery_rate).all()
    
    recommended_questions = []
    
    if weak_points:
        # 优先从薄弱知识点中选题
        for wp in weak_points:
            kp_questions = Question.query.filter_by(
                subject=subject,
                knowledge_point=wp.knowledge_point
            ).all()
            
            if kp_questions:
                # 每个薄弱点选2-3题
                sample_count = min(3, len(kp_questions), count - len(recommended_questions))
                selected = random.sample(kp_questions, sample_count)
                recommended_questions.extend(selected)
                
                if len(recommended_questions) >= count:
                    break
    else:
        # 没有薄弱点，随机选题
        all_questions = Question.query.filter_by(subject=subject).all()
        if all_questions:
            recommended_questions = random.sample(all_questions, min(count, len(all_questions)))
    
    # 如果还不够，补充其他题目
    if len(recommended_questions) < count:
        remaining = count - len(recommended_questions)
        existing_ids = [q.id for q in recommended_questions]
        other_questions = Question.query.filter(
            Question.subject == subject,
            ~Question.id.in_(existing_ids)
        ).limit(remaining).all()
        recommended_questions.extend(other_questions)
    
    result = []
    for q in recommended_questions:
        result.append({
            'id': q.id,
            'subject': q.subject,
            'knowledge_point': q.knowledge_point,
            'difficulty': q.difficulty,
            'question_type': q.question_type,
            'content': q.content,
            'options': json.loads(q.options) if q.options else None
        })
    
    return jsonify({
        'code': 200,
        'message': '推荐成功',
        'data': {
            'questions': result,
            'weak_points_focused': [wp.knowledge_point for wp in weak_points[:5]] if weak_points else []
        }
    })

@bp.route('/submit-answer', methods=['POST'])
@token_required
def submit_answer(current_user):
    """提交答案并判分"""
    data = request.get_json()
    question_id = data.get('question_id')
    user_answer = data.get('answer')
    answer_time = data.get('answer_time', 0)
    
    if not question_id or user_answer is None:
        return jsonify({'code': 400, 'message': '参数不完整', 'data': None}), 400
    
    question = Question.query.get(question_id)
    if not question:
        return jsonify({'code': 404, 'message': '题目不存在', 'data': None}), 404
    
    # 判断答案是否正确
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
    
    # 更新知识点掌握度
    mastery = UserKnowledgeMastery.query.filter_by(
        user_id=current_user['user_id'],
        knowledge_point=question.knowledge_point
    ).first()
    
    if mastery:
        mastery.total_questions += 1
        if is_correct:
            mastery.correct_questions += 1
        mastery.mastery_rate = (mastery.correct_questions / mastery.total_questions) * 100
    else:
        new_mastery = UserKnowledgeMastery(
            user_id=current_user['user_id'],
            knowledge_point=question.knowledge_point,
            subject=question.subject,
            total_questions=1,
            correct_questions=1 if is_correct else 0,
            mastery_rate=100 if is_correct else 0
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
    
    return jsonify({
        'code': 200,
        'message': '提交成功',
        'data': {
            'is_correct': is_correct,
            'correct_answer': question.answer,
            'analysis': question.analysis,
            'knowledge_point': question.knowledge_point
        }
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
    
    # 总学习时长（秒）
    total_time = db.session.query(func.sum(StudyRecord.answer_time)).filter_by(
        user_id=current_user['user_id']
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
