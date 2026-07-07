"""
Dashboard 首页蓝图
所有统计计算逻辑已移入 services/stat_service.py
"""

from flask import Blueprint

from app.models import db, StudyRecord, UserKnowledgeMastery
from app.utils.jwt_util import login_required
from app.utils.response_util import success
from app.services.stat_service import StatService

bp = Blueprint('dashboard', __name__)


@bp.route('/overview', methods=['GET'])
@login_required
def get_dashboard_overview(current_user):
    """获取首页概览数据"""
    data = StatService.get_dashboard_overview(current_user['user_id'])
    return success(data=data)


@bp.route('/daily-trend', methods=['GET'])
@login_required
def get_daily_trend(current_user):
    """获取最近7天刷题趋势"""
    dates, counts, accuracies = StatService.get_dashboard_daily_trend(
        current_user['user_id']
    )
    return success(data={
        'dates': dates,
        'practice_counts': counts,
        'accuracy_rates': accuracies,
    })


@bp.route('/weak-points', methods=['GET'])
@login_required
def get_dashboard_weak_points(current_user):
    """获取首页展示的薄弱知识点TOP5"""
    result = StatService.get_dashboard_weak_points(current_user['user_id'])
    return success(data=result)


@bp.route('/recent-activity', methods=['GET'])
@login_required
def get_recent_activity(current_user):
    """获取最近学习活动"""
    recent_records = StudyRecord.query.filter_by(
        user_id=current_user['user_id']
    ).order_by(StudyRecord.created_at.desc()).limit(10).all()

    result = []
    for record in recent_records:
        result.append({
            'type': record.study_type,
            'is_correct': record.is_correct,
            'time': record.created_at.strftime('%H:%M'),
            'date': record.created_at.strftime('%m-%d'),
        })

    return success(data=result)
