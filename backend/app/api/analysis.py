import os
import json
import uuid
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from datetime import datetime, date, timedelta

from app.models import db, ExamPaper, UserKnowledgeMastery, Question, StudyRecord, WrongQuestion, Subject
from app.utils.jwt_auth import token_required

bp = Blueprint('analysis', __name__)
ocr_service = None

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

def get_ocr_service():
    global ocr_service
    if ocr_service is None:
        from app.utils.ocr_service import OCRService
        ocr_service = OCRService()
    return ocr_service

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/upload', methods=['POST'])
@token_required
def upload_exam_paper(current_user):
    """上传试卷并进行OCR识别"""
    if 'file' not in request.files:
        return jsonify({'code': 400, 'message': '没有上传文件', 'data': None}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'code': 400, 'message': '没有选择文件', 'data': None}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'code': 400, 'message': '不支持的文件格式', 'data': None}), 400
    
    # 保存文件
    filename = secure_filename(f"{uuid.uuid4().hex}_{file.filename}")
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    # OCR识别
    subject = request.form.get('subject', '数学')
    title = request.form.get('title', '未命名试卷')
    
    try:
        service = get_ocr_service()
        ocr_text = service.recognize_image(filepath)
        # 从数据库读取该科目配置的关键词
        subject_record = Subject.query.filter_by(name=subject, is_active=True).first()
        keywords = json.loads(subject_record.keywords) if subject_record and subject_record.keywords else None
        analysis_result = service.generate_analysis_report(ocr_text, subject, keywords)
    except Exception as e:
        return jsonify({'code': 500, 'message': 'OCR 服务初始化失败，请检查 PaddleOCR 配置', 'data': str(e)}), 500
    
    # 保存到数据库
    exam_paper = ExamPaper(
        user_id=current_user['user_id'],
        title=title,
        subject=subject,
        image_path=filepath,
        ocr_content=ocr_text,
        analysis_result=json.dumps(analysis_result, ensure_ascii=False),
        knowledge_points=json.dumps(analysis_result['knowledge_points'], ensure_ascii=False),
        mastery_level=json.dumps(analysis_result['mastery_level'], ensure_ascii=False)
    )
    
    db.session.add(exam_paper)
    
    # 更新用户知识点掌握度
    for kp, mastery in analysis_result['mastery_level'].items():
        existing = UserKnowledgeMastery.query.filter_by(
            user_id=current_user['user_id'],
            knowledge_point=kp
        ).first()
        
        if existing:
            # 加权平均更新
            existing.mastery_rate = (existing.mastery_rate + mastery) / 2
            existing.total_questions += 5
            existing.correct_questions += int(5 * mastery / 100)
        else:
            new_mastery = UserKnowledgeMastery(
                user_id=current_user['user_id'],
                knowledge_point=kp,
                subject=subject,
                total_questions=10,
                correct_questions=int(10 * mastery / 100),
                mastery_rate=mastery
            )
            db.session.add(new_mastery)
    
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': '分析完成',
        'data': {
            'paper_id': exam_paper.id,
            'title': title,
            'subject': subject,
            'knowledge_points': analysis_result['knowledge_points'],
            'mastery_level': analysis_result['mastery_level'],
            'weak_points': analysis_result['weak_points'],
            'suggestions': analysis_result['suggestions'],
            'ocr_preview': ocr_text[:500] + '...' if len(ocr_text) > 500 else ocr_text
        }
    })

@bp.route('/history', methods=['GET'])
@token_required
def get_analysis_history(current_user):
    """获取学情分析历史记录"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)
    
    query = ExamPaper.query.filter_by(user_id=current_user['user_id']).order_by(ExamPaper.created_at.desc())
    total = query.count()
    papers = query.offset((page - 1) * page_size).limit(page_size).all()
    
    result = []
    for paper in papers:
        result.append({
            'id': paper.id,
            'title': paper.title,
            'subject': paper.subject,
            'created_at': paper.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'knowledge_count': len(json.loads(paper.knowledge_points)) if paper.knowledge_points else 0
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

@bp.route('/detail/<int:paper_id>', methods=['GET'])
@token_required
def get_analysis_detail(current_user, paper_id):
    """获取学情分析详情"""
    paper = ExamPaper.query.filter_by(id=paper_id, user_id=current_user['user_id']).first()
    
    if not paper:
        return jsonify({'code': 404, 'message': '记录不存在', 'data': None}), 404
    
    analysis_result = json.loads(paper.analysis_result) if paper.analysis_result else {}
    mastery_level = json.loads(paper.mastery_level) if paper.mastery_level else {}
    
    return jsonify({
        'code': 200,
        'message': '获取成功',
        'data': {
            'id': paper.id,
            'title': paper.title,
            'subject': paper.subject,
            'knowledge_points': json.loads(paper.knowledge_points) if paper.knowledge_points else [],
            'mastery_level': mastery_level,
            'weak_points': analysis_result.get('weak_points', []),
            'suggestions': analysis_result.get('suggestions', []),
            'ocr_content': paper.ocr_content,
            'created_at': paper.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    })

@bp.route('/delete/<int:paper_id>', methods=['DELETE'])
@token_required
def delete_analysis(current_user, paper_id):
    """删除学情分析记录"""
    paper = ExamPaper.query.filter_by(id=paper_id, user_id=current_user['user_id']).first()

    if not paper:
        return jsonify({'code': 404, 'message': '记录不存在', 'data': None}), 404

    # 删除图片文件
    if paper.image_path and os.path.exists(paper.image_path):
        try:
            os.remove(paper.image_path)
        except OSError:
            pass

    db.session.delete(paper)
    db.session.commit()

    return jsonify({
        'code': 200,
        'message': '删除成功',
        'data': None
    })

@bp.route('/knowledge-mastery', methods=['GET'])
@token_required
def get_knowledge_mastery(current_user):
    """获取用户知识点掌握度（用于雷达图）"""
    subject = request.args.get('subject', '数学')
    
    mastery_records = UserKnowledgeMastery.query.filter_by(
        user_id=current_user['user_id'],
        subject=subject
    ).all()
    
    # 如果没有数据，返回默认数据
    if not mastery_records:
        default_points = ['函数', '导数', '数列', '三角函数', '立体几何', '解析几何']
        result = {
            'indicators': default_points,
            'data': [75, 65, 70, 80, 60, 72]
        }
    else:
        # 取前6个知识点
        sorted_records = sorted(mastery_records, key=lambda x: x.mastery_rate, reverse=True)[:6]
        result = {
            'indicators': [r.knowledge_point for r in sorted_records],
            'data': [round(r.mastery_rate, 1) for r in sorted_records]
        }
    
    return jsonify({
        'code': 200,
        'message': '获取成功',
        'data': result
    })


@bp.route('/ai-report', methods=['GET'])
@token_required
def generate_ai_report(current_user):
    """生成 AI 个性化学习报告"""
    from sqlalchemy import func
    from app.utils.ai_question_service import AIQuestionService

    user_id = current_user['user_id']
    subject = request.args.get('subject', '')

    # ========== 1. 收集学习数据 ==========

    # 知识点掌握度
    mastery_query = UserKnowledgeMastery.query.filter_by(user_id=user_id)
    if subject:
        mastery_query = mastery_query.filter_by(subject=subject)
    mastery_records = mastery_query.all()

    mastery_data = []
    for m in mastery_records:
        mastery_data.append({
            'knowledge_point': m.knowledge_point,
            'subject': m.subject,
            'mastery_rate': round(m.mastery_rate, 1),
            'total_questions': m.total_questions,
            'correct_questions': m.correct_questions
        })

    # 近7天刷题趋势
    seven_days_ago = date.today() - timedelta(days=6)
    daily_stats = []
    for i in range(7):
        day = seven_days_ago + timedelta(days=i)
        total = StudyRecord.query.filter_by(user_id=user_id, study_type='practice').filter(
            func.date(StudyRecord.created_at) == day
        ).count()
        correct = StudyRecord.query.filter_by(user_id=user_id, study_type='practice', is_correct=True).filter(
            func.date(StudyRecord.created_at) == day
        ).count()
        daily_stats.append({
            'date': day.strftime('%m-%d'),
            'total': total,
            'correct': correct,
            'accuracy': round(correct / total * 100, 1) if total > 0 else 0
        })

    # 总体统计
    total_practice = StudyRecord.query.filter_by(user_id=user_id, study_type='practice').count()
    total_correct = StudyRecord.query.filter_by(user_id=user_id, study_type='practice', is_correct=True).count()
    overall_accuracy = round(total_correct / total_practice * 100, 1) if total_practice > 0 else 0

    # 待复习错题
    pending_wrong = WrongQuestion.query.filter_by(user_id=user_id, status='pending').order_by(
        WrongQuestion.wrong_count.desc()
    ).limit(5).all()
    wrong_list = []
    for w in pending_wrong:
        q = Question.query.get(w.question_id)
        if q:
            wrong_list.append({
                'content': q.content[:60],
                'knowledge_point': q.knowledge_point,
                'wrong_count': w.wrong_count
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
            'created_at': p.created_at.strftime('%Y-%m-%d')
        })

    # ========== 2. 调用 AI 生成报告 ==========

    data_context = f"""
【学生学习数据概览】
- 总刷题数：{total_practice} 道
- 总正确率：{overall_accuracy}%
- 待复习错题：{WrongQuestion.query.filter_by(user_id=user_id, status='pending').count()} 道

【知识点掌握情况】（共 {len(mastery_data)} 个知识点）
"""
    for m in sorted(mastery_data, key=lambda x: x['mastery_rate']):
        data_context += f"  - {m['subject']}/{m['knowledge_point']}：掌握度 {m['mastery_rate']}%（练习{m['total_questions']}题，正确{m['correct_questions']}题）\n"

    data_context += "\n【近7天刷题趋势】\n"
    for d in daily_stats:
        data_context += f"  - {d['date']}：{d['total']}题，正确率{d['accuracy']}%\n"

    if wrong_list:
        data_context += "\n【待复习错题TOP5】\n"
        for w in wrong_list:
            data_context += f"  - [{w['knowledge_point']}] {w['content']}...（错{w['wrong_count']}次）\n"

    if paper_summaries:
        data_context += "\n【最近试卷分析】\n"
        for p in paper_summaries:
            weak = '、'.join(p['weak_points']) if p['weak_points'] else '无'
            data_context += f"  - {p['title']}（{p['subject']}，{p['created_at']}）薄弱点：{weak}\n"

    if not mastery_data and total_practice == 0:
        data_context += "\n（该学生尚未进行过任何练习或试卷分析）\n"

    prompt = f"""你是一位专业的学习分析师，请根据以下学生学习数据生成一份个性化的学习报告。

{data_context}

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

    try:
        ai = AIQuestionService()
        response = ai.client.chat.completions.create(
            model=ai.model,
            messages=[
                {"role": "system", "content": "你是一位专业的教育学习分析师，只输出JSON格式的报告，不输出任何其他内容。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2048
        )

        content = response.choices[0].message.content
        report = ai._parse_report_json(content)

        return jsonify({
            'code': 200,
            'message': '报告生成成功',
            'data': {
                'report': report,
                'stats': {
                    'total_practice': total_practice,
                    'overall_accuracy': overall_accuracy,
                    'mastery_count': len(mastery_data),
                    'weak_count': len([m for m in mastery_data if m['mastery_rate'] < 70])
                }
            }
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': f'AI 报告生成失败: {str(e)}', 'data': None}), 500

@bp.route('/weak-points', methods=['GET'])
@token_required
def get_weak_points(current_user):
    """获取用户薄弱知识点"""
    subject = request.args.get('subject', '数学')
    
    mastery_records = UserKnowledgeMastery.query.filter_by(
        user_id=current_user['user_id'],
        subject=subject
    ).all()
    
    # 找出掌握度低于70的薄弱点
    weak_points = []
    for record in mastery_records:
        if record.mastery_rate < 70:
            weak_points.append({
                'knowledge_point': record.knowledge_point,
                'mastery_rate': round(record.mastery_rate, 1),
                'subject': record.subject
            })
    
    # 按掌握度升序排列
    weak_points.sort(key=lambda x: x['mastery_rate'])
    
    return jsonify({
        'code': 200,
        'message': '获取成功',
        'data': weak_points[:10]  # 返回前10个薄弱点
    })
