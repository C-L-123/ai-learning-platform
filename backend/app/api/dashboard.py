from flask import Blueprint, request, jsonify
from sqlalchemy import func
from datetime import date, datetime, timedelta

from app.models import db, StudyRecord, WrongQuestion, UserKnowledgeMastery
from app.utils.jwt_auth import token_required

bp = Blueprint('dashboard', __name__)

@bp.route('/overview', methods=['GET'])
@token_required
def get_dashboard_overview(current_user):
    """获取首页概览数据"""
    user_id = current_user['user_id']
    
    # 1. 累计刷题总数
    total_practice = StudyRecord.query.filter_by(
        user_id=user_id,
        study_type='practice'
    ).count()
    
    # 2. 总体正确率
    correct_count = StudyRecord.query.filter_by(
        user_id=user_id,
        study_type='practice',
        is_correct=True
    ).count()
    accuracy = (correct_count / total_practice * 100) if total_practice > 0 else 0
    
    # 3. 累计学习时长（分钟）
    total_seconds = db.session.query(func.sum(StudyRecord.answer_time)).filter_by(
        user_id=user_id
    ).scalar() or 0
    total_minutes = int(total_seconds / 60)
    
    # 4. 待复习错题数量
    pending_wrong = WrongQuestion.query.filter_by(
        user_id=user_id,
        status='pending'
    ).count()
    
    # 5. 今日数据
    today = date.today()
    today_practice = StudyRecord.query.filter_by(
        user_id=user_id,
        study_type='practice'
    ).filter(func.date(StudyRecord.created_at) == today).count()
    
    today_correct = StudyRecord.query.filter_by(
        user_id=user_id,
        study_type='practice',
        is_correct=True
    ).filter(func.date(StudyRecord.created_at) == today).count()
    today_accuracy = (today_correct / today_practice * 100) if today_practice > 0 else 0
    
    return jsonify({
        'code': 200,
        'message': '获取成功',
        'data': {
            'stats_cards': {
                'total_practice': total_practice,
                'overall_accuracy': round(accuracy, 1),
                'total_study_minutes': total_minutes,
                'pending_wrong_count': pending_wrong
            },
            'today_stats': {
                'practice_count': today_practice,
                'accuracy': round(today_accuracy, 1)
            }
        }
    })

@bp.route('/daily-trend', methods=['GET'])
@token_required
def get_daily_trend(current_user):
    """获取最近7天刷题趋势"""
    user_id = current_user['user_id']
    days = 7
    
    dates = []
    practice_counts = []
    accuracy_rates = []
    
    for i in range(days - 1, -1, -1):
        day = date.fromordinal(date.today().toordinal() - i)
        day_str = day.strftime('%m-%d')
        
        day_count = StudyRecord.query.filter_by(
            user_id=user_id,
            study_type='practice'
        ).filter(func.date(StudyRecord.created_at) == day).count()
        
        day_correct = StudyRecord.query.filter_by(
            user_id=user_id,
            study_type='practice',
            is_correct=True
        ).filter(func.date(StudyRecord.created_at) == day).count()
        
        accuracy = (day_correct / day_count * 100) if day_count > 0 else 0
        
        dates.append(day_str)
        practice_counts.append(day_count)
        accuracy_rates.append(round(accuracy, 1))
    
    return jsonify({
        'code': 200,
        'message': '获取成功',
        'data': {
            'dates': dates,
            'practice_counts': practice_counts,
            'accuracy_rates': accuracy_rates
        }
    })

@bp.route('/weak-points', methods=['GET'])
@token_required
def get_dashboard_weak_points(current_user):
    """获取首页展示的薄弱知识点TOP5"""
    user_id = current_user['user_id']
    
    weak_points = UserKnowledgeMastery.query.filter_by(
        user_id=user_id
    ).filter(
        UserKnowledgeMastery.mastery_rate < 75
    ).order_by(UserKnowledgeMastery.mastery_rate).limit(5).all()
    
    result = []
    for wp in weak_points:
        result.append({
            'knowledge_point': wp.knowledge_point,
            'subject': wp.subject,
            'mastery_rate': round(wp.mastery_rate, 1)
        })
    
    return jsonify({
        'code': 200,
        'message': '获取成功',
        'data': result
    })

@bp.route('/recent-activity', methods=['GET'])
@token_required
def get_recent_activity(current_user):
    """获取最近学习活动"""
    user_id = current_user['user_id']
    
    recent_records = StudyRecord.query.filter_by(
        user_id=user_id
    ).order_by(StudyRecord.created_at.desc()).limit(10).all()
    
    result = []
    for record in recent_records:
        result.append({
            'type': record.study_type,
            'is_correct': record.is_correct,
            'time': record.created_at.strftime('%H:%M'),
            'date': record.created_at.strftime('%m-%d')
        })
    
    return jsonify({
        'code': 200,
        'message': '获取成功',
        'data': result
    })
