import os
import json
import uuid
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from datetime import datetime

from app.models import db, ExamPaper, UserKnowledgeMastery, Question
from app.utils.jwt_auth import token_required
from app.utils.ocr_service import OCRService

bp = Blueprint('analysis', __name__)
ocr_service = None

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

def get_ocr_service():
    global ocr_service
    if ocr_service is None:
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
        analysis_result = service.generate_analysis_report(ocr_text, subject)
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
