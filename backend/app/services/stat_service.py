"""
学情统计业务服务层
封装所有统计计算：首页概览、刷题统计、每日趋势、薄弱知识点、AI 报告数据收集
所有统计逻辑集中于此，路由层只负责调用和返回
"""

import json
from datetime import date, timedelta
from sqlalchemy import func

from app.models import (
    db, StudyRecord, WrongQuestion, UserKnowledgeMastery,
    Question, ExamPaper,
)


class StatService:
    """学情统计业务服务"""

    # ==================== Dashboard ====================

    @staticmethod
    def get_dashboard_overview(user_id):
        """首页概览：累计刷题、正确率、学习时长、今日数据"""
        today = date.today()

        total_practice = StudyRecord.query.filter_by(
            user_id=user_id, study_type='practice'
        ).count()

        correct_count = StudyRecord.query.filter_by(
            user_id=user_id, study_type='practice', is_correct=True
        ).count()
        accuracy = (correct_count / total_practice * 100) if total_practice > 0 else 0

        total_seconds = db.session.query(
            func.sum(StudyRecord.answer_time)
        ).filter_by(
            user_id=user_id, study_type='practice_session'
        ).scalar() or 0

        pending_wrong = WrongQuestion.query.filter_by(
            user_id=user_id, status='pending'
        ).count()

        today_practice = StudyRecord.query.filter_by(
            user_id=user_id, study_type='practice'
        ).filter(
            func.date(StudyRecord.created_at) == today
        ).count()

        today_correct = StudyRecord.query.filter_by(
            user_id=user_id, study_type='practice', is_correct=True
        ).filter(
            func.date(StudyRecord.created_at) == today
        ).count()
        today_accuracy = (today_correct / today_practice * 100) if today_practice > 0 else 0

        return {
            'stats_cards': {
                'total_practice': total_practice,
                'overall_accuracy': round(accuracy, 1),
                'total_study_minutes': int(total_seconds / 60),
                'pending_wrong_count': pending_wrong,
            },
            'today_stats': {
                'practice_count': today_practice,
                'accuracy': round(today_accuracy, 1),
            },
        }

    # ==================== Practice ====================

    @staticmethod
    def get_practice_stats(user_id):
        """刷题统计数据：总数、正确率、今日数、学习时长"""
        today = date.today()

        total_practice = StudyRecord.query.filter_by(
            user_id=user_id, study_type='practice'
        ).count()

        correct_count = StudyRecord.query.filter_by(
            user_id=user_id, study_type='practice', is_correct=True
        ).count()

        today_count = StudyRecord.query.filter_by(
            user_id=user_id, study_type='practice'
        ).filter(
            func.date(StudyRecord.created_at) == today
        ).count()

        total_time = db.session.query(
            func.sum(StudyRecord.answer_time)
        ).filter_by(
            user_id=user_id, study_type='practice_session'
        ).scalar() or 0

        accuracy = (correct_count / total_practice * 100) if total_practice > 0 else 0

        return {
            'total_practice': total_practice,
            'correct_count': correct_count,
            'accuracy': round(accuracy, 1),
            'today_count': today_count,
            'total_study_time': total_time,
        }

    @staticmethod
    def get_daily_trend(user_id, days=7):
        """每日刷题趋势（最近 N 天）"""
        trend_data = []

        for i in range(days - 1, -1, -1):
            day = date.fromordinal(date.today().toordinal() - i)
            day_str = day.strftime('%m-%d')

            day_count = StudyRecord.query.filter_by(
                user_id=user_id, study_type='practice'
            ).filter(
                func.date(StudyRecord.created_at) == day
            ).count()

            day_correct = StudyRecord.query.filter_by(
                user_id=user_id, study_type='practice', is_correct=True
            ).filter(
                func.date(StudyRecord.created_at) == day
            ).count()

            accuracy = (day_correct / day_count * 100) if day_count > 0 else 0

            trend_data.append({
                'date': day_str,
                'count': day_count,
                'accuracy': round(accuracy, 1),
            })

        return trend_data

    # ==================== Weak Points ====================

    @staticmethod
    def get_weak_points(user_id, subject='数学', threshold=70, limit=10):
        """薄弱知识点列表"""
        mastery_records = UserKnowledgeMastery.query.filter_by(
            user_id=user_id, subject=subject
        ).all()

        weak_points = []
        for record in mastery_records:
            if record.mastery_rate < threshold:
                weak_points.append({
                    'knowledge_point': record.knowledge_point,
                    'mastery_rate': round(record.mastery_rate, 1),
                    'subject': record.subject,
                })

        weak_points.sort(key=lambda x: x['mastery_rate'])
        return weak_points[:limit]

    @staticmethod
    def get_dashboard_weak_points(user_id, threshold=75, limit=5):
        """首页展示的薄弱知识点 TOP N（不限科目）"""
        weak_points = UserKnowledgeMastery.query.filter_by(
            user_id=user_id
        ).filter(
            UserKnowledgeMastery.mastery_rate < threshold
        ).order_by(UserKnowledgeMastery.mastery_rate).limit(limit).all()

        return [
            {
                'knowledge_point': wp.knowledge_point,
                'subject': wp.subject,
                'mastery_rate': round(wp.mastery_rate, 1),
            }
            for wp in weak_points
        ]

    @staticmethod
    def get_dashboard_daily_trend(user_id, days=7):
        """首页每日刷题趋势（返回三个列表，方便 ECharts 渲染）"""
        dates = []
        practice_counts = []
        accuracy_rates = []

        for i in range(days - 1, -1, -1):
            day = date.fromordinal(date.today().toordinal() - i)
            day_str = day.strftime('%m-%d')

            day_count = StudyRecord.query.filter_by(
                user_id=user_id, study_type='practice'
            ).filter(
                func.date(StudyRecord.created_at) == day
            ).count()

            day_correct = StudyRecord.query.filter_by(
                user_id=user_id, study_type='practice', is_correct=True
            ).filter(
                func.date(StudyRecord.created_at) == day
            ).count()

            accuracy = (day_correct / day_count * 100) if day_count > 0 else 0

            dates.append(day_str)
            practice_counts.append(day_count)
            accuracy_rates.append(round(accuracy, 1))

        return dates, practice_counts, accuracy_rates

    @staticmethod
    def get_knowledge_mastery(user_id, subject='数学'):
        """知识点掌握度（雷达图数据）"""
        mastery_records = UserKnowledgeMastery.query.filter_by(
            user_id=user_id, subject=subject
        ).all()

        if not mastery_records:
            default_points = ['函数', '导数', '数列', '三角函数', '立体几何', '解析几何']
            return {
                'indicators': default_points,
                'data': [75, 65, 70, 80, 60, 72],
            }

        sorted_records = sorted(
            mastery_records, key=lambda x: x.mastery_rate, reverse=True
        )[:6]
        return {
            'indicators': [r.knowledge_point for r in sorted_records],
            'data': [round(r.mastery_rate, 1) for r in sorted_records],
        }

    # ==================== AI Report ====================

    @staticmethod
    def collect_report_data(user_id, subject=''):
        """收集 AI 报告所需的全部学习数据

        返回结构化字典，供 LLM 提示词组装使用
        """
        seven_days_ago = date.today() - timedelta(days=6)

        # 知识点掌握度
        mastery_query = UserKnowledgeMastery.query.filter_by(user_id=user_id)
        if subject:
            mastery_query = mastery_query.filter_by(subject=subject)
        mastery_records = mastery_query.all()

        mastery_data = [
            {
                'knowledge_point': m.knowledge_point,
                'subject': m.subject,
                'mastery_rate': round(m.mastery_rate, 1),
                'total_questions': m.total_questions,
                'correct_questions': m.correct_questions,
            }
            for m in mastery_records
        ]

        # 近7天刷题趋势
        daily_stats = []
        for i in range(7):
            day = seven_days_ago + timedelta(days=i)
            total = StudyRecord.query.filter_by(
                user_id=user_id, study_type='practice'
            ).filter(func.date(StudyRecord.created_at) == day).count()
            correct = StudyRecord.query.filter_by(
                user_id=user_id, study_type='practice', is_correct=True
            ).filter(func.date(StudyRecord.created_at) == day).count()
            daily_stats.append({
                'date': day.strftime('%m-%d'),
                'total': total,
                'correct': correct,
                'accuracy': round(correct / total * 100, 1) if total > 0 else 0,
            })

        # 总体统计
        total_practice = StudyRecord.query.filter_by(
            user_id=user_id, study_type='practice'
        ).count()
        total_correct = StudyRecord.query.filter_by(
            user_id=user_id, study_type='practice', is_correct=True
        ).count()
        overall_accuracy = (
            round(total_correct / total_practice * 100, 1) if total_practice > 0 else 0
        )

        # 待复习错题 TOP5
        pending_wrong = WrongQuestion.query.filter_by(
            user_id=user_id, status='pending'
        ).order_by(WrongQuestion.wrong_count.desc()).limit(5).all()

        wrong_list = []
        for w in pending_wrong:
            q = Question.query.get(w.question_id)
            if q:
                wrong_list.append({
                    'content': q.content[:60],
                    'knowledge_point': q.knowledge_point,
                    'wrong_count': w.wrong_count,
                })

        # 最近试卷分析
        recent_papers = ExamPaper.query.filter_by(user_id=user_id).order_by(
            ExamPaper.created_at.desc()
        ).limit(3).all()

        paper_summaries = []
        for p in recent_papers:
            analysis = json.loads(p.analysis_result) if p.analysis_result else {}
            paper_summaries.append({
                'title': p.title,
                'subject': p.subject,
                'weak_points': analysis.get('weak_points', []),
                'created_at': p.created_at.strftime('%Y-%m-%d'),
            })

        pending_wrong_count = WrongQuestion.query.filter_by(
            user_id=user_id, status='pending'
        ).count()

        return {
            'mastery_data': mastery_data,
            'daily_stats': daily_stats,
            'total_practice': total_practice,
            'overall_accuracy': overall_accuracy,
            'wrong_list': wrong_list,
            'paper_summaries': paper_summaries,
            'pending_wrong_count': pending_wrong_count,
        }
