"""
学情分析蓝图（非 OCR 部分）
OCR 上传已移至 ocr.py
本文件：历史记录、详情、删除、知识点掌握度、AI 报告、薄弱知识点
"""

import os
import json
from flask import Blueprint, request

from app.models import db, ExamPaper
from app.utils.jwt_util import login_required
from app.utils.response_util import success, fail
from app.services.stat_service import StatService
from app.services.llm_service import LLMService

bp = Blueprint('analysis', __name__)


# ==================== AI 报告辅助函数 ====================

def _build_report_prompt(data):
    """根据收集的学习数据构建 AI 报告提示词"""
    mastery_data = data['mastery_data']
    daily_stats = data['daily_stats']
    total_practice = data['total_practice']
    overall_accuracy = data['overall_accuracy']
    wrong_list = data['wrong_list']
    paper_summaries = data['paper_summaries']
    pending_wrong_count = data['pending_wrong_count']

    ctx = f"""
【学生学习数据概览】
- 总刷题数：{total_practice} 道
- 总正确率：{overall_accuracy}%
- 待复习错题：{pending_wrong_count} 道

【知识点掌握情况】（共 {len(mastery_data)} 个知识点）
"""
    for m in sorted(mastery_data, key=lambda x: x['mastery_rate']):
        ctx += (
            f"  - {m['subject']}/{m['knowledge_point']}：掌握度 "
            f"{m['mastery_rate']}%（练习{m['total_questions']}题，"
            f"正确{m['correct_questions']}题）\n"
        )

    ctx += "\n【近7天刷题趋势】\n"
    for d in daily_stats:
        ctx += f"  - {d['date']}：{d['total']}题，正确率{d['accuracy']}%\n"

    if wrong_list:
        ctx += "\n【待复习错题TOP5】\n"
        for w in wrong_list:
            ctx += f"  - [{w['knowledge_point']}] {w['content']}...（错{w['wrong_count']}次）\n"

    if paper_summaries:
        ctx += "\n【最近试卷分析】\n"
        for p in paper_summaries:
            weak = '、'.join(p['weak_points']) if p['weak_points'] else '无'
            ctx += f"  - {p['title']}（{p['subject']}，{p['created_at']}）薄弱点：{weak}\n"

    if not mastery_data and total_practice == 0:
        ctx += "\n（该学生尚未进行过任何练习或试卷分析）\n"

    prompt = f"""你是一位专业的学习分析师，请根据以下学生学习数据生成一份个性化的学习报告。

{ctx}

请严格按以下 JSON 格式返回，不要输出任何其他内容：
```json
{{
  "summary": "总体评价（2-3句话，概括学习状态）",
  "progress": "进步与变化分析（分析最近的趋势，哪些有进步、哪些退步）",
  "weak_analysis": "薄弱知识点深度分析（针对掌握度低的知识点给出具体分析）",
  "suggestions": ["建议1", "建议2", "建议3"],
  "study_plan": "下一步学习计划（具体可执行的建议）"
}}
```

要求：
- 语气亲切、鼓励性
- 分析要具体，引用实际数据
- 建议要可操作，不要太笼统
- 如果数据较少，给出引导性建议"""

    return ctx, prompt


# ==================== 路由 ====================

@bp.route('/history', methods=['GET'])
@login_required
def get_analysis_history(current_user):
    """获取学情分析历史记录"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)

    query = ExamPaper.query.filter_by(
        user_id=current_user['user_id']
    ).order_by(ExamPaper.created_at.desc())
    total = query.count()
    papers = query.offset((page - 1) * page_size).limit(page_size).all()

    result = []
    for paper in papers:
        result.append({
            'id': paper.id,
            'title': paper.title,
            'subject': paper.subject,
            'created_at': paper.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'knowledge_count': (
                len(json.loads(paper.knowledge_points))
                if paper.knowledge_points else 0
            ),
        })

    return success(data={
        'list': result,
        'total': total,
        'page': page,
        'page_size': page_size,
    })


@bp.route('/detail/<int:paper_id>', methods=['GET'])
@login_required
def get_analysis_detail(current_user, paper_id):
    """获取学情分析详情"""
    paper = ExamPaper.query.filter_by(
        id=paper_id, user_id=current_user['user_id']
    ).first()

    if not paper:
        return fail(message='记录不存在', code=404)

    analysis_result = json.loads(paper.analysis_result) if paper.analysis_result else {}
    mastery_level = json.loads(paper.mastery_level) if paper.mastery_level else {}

    return success(data={
        'id': paper.id,
        'title': paper.title,
        'subject': paper.subject,
        'knowledge_points': (
            json.loads(paper.knowledge_points) if paper.knowledge_points else []
        ),
        'mastery_level': mastery_level,
        'weak_points': analysis_result.get('weak_points', []),
        'suggestions': analysis_result.get('suggestions', []),
        'ocr_content': paper.ocr_content,
        'created_at': paper.created_at.strftime('%Y-%m-%d %H:%M:%S'),
    })


@bp.route('/delete/<int:paper_id>', methods=['DELETE'])
@login_required
def delete_analysis(current_user, paper_id):
    """删除学情分析记录"""
    paper = ExamPaper.query.filter_by(
        id=paper_id, user_id=current_user['user_id']
    ).first()

    if not paper:
        return fail(message='记录不存在', code=404)

    if paper.image_path and os.path.exists(paper.image_path):
        try:
            os.remove(paper.image_path)
        except OSError:
            pass

    db.session.delete(paper)
    db.session.commit()

    return success(message='删除成功')


@bp.route('/knowledge-mastery', methods=['GET'])
@login_required
def get_knowledge_mastery(current_user):
    """获取用户知识点掌握度（用于雷达图）"""
    subject = request.args.get('subject', '数学')
    result = StatService.get_knowledge_mastery(current_user['user_id'], subject)
    return success(data=result)


@bp.route('/ai-report', methods=['GET'])
@login_required
def generate_ai_report(current_user):
    """生成 AI 个性化学习报告"""
    subject = request.args.get('subject', '')
    user_id = current_user['user_id']

    # 1. 收集学习数据（stat_service）
    data = StatService.collect_report_data(user_id, subject)

    # 2. 构建提示词
    data_context, prompt = _build_report_prompt(data)

    # 3. 调用 AI 生成报告（llm_service）
    try:
        report = LLMService.generate_study_report(data_context, prompt)

        weak_count = len(
            [m for m in data['mastery_data'] if m['mastery_rate'] < 70]
        )

        return success(data={
            'report': report,
            'stats': {
                'total_practice': data['total_practice'],
                'overall_accuracy': data['overall_accuracy'],
                'mastery_count': len(data['mastery_data']),
                'weak_count': weak_count,
            },
        }, message='报告生成成功')
    except Exception as e:
        return fail(message=f'AI 报告生成失败: {str(e)}', code=500)


@bp.route('/weak-points', methods=['GET'])
@login_required
def get_weak_points(current_user):
    """获取用户薄弱知识点"""
    subject = request.args.get('subject', '数学')
    result = StatService.get_weak_points(current_user['user_id'], subject)
    return success(data=result)
