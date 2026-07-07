"""
OCR 上传蓝图
仅保留：鉴权 → 文件校验 → 调用 ocr_service → 保存数据库 → 返回
识别代码全部在 services/ocr_service.py 中
"""

import os
import json
import logging
from flask import Blueprint, request, current_app

from app.models import db, ExamPaper, UserKnowledgeMastery
from app.utils.jwt_util import login_required
from app.utils.response_util import success, fail
from app.utils.file_util import validate_image_file
from app.services.ocr_service import OCRBusinessService

logger = logging.getLogger(__name__)

# 蓝图名称不同于 analysis 蓝图，URL 前缀相同 → 前端无需改动
bp = Blueprint('analysis_ocr', __name__)


@bp.route('/upload', methods=['POST'])
@login_required
def upload_exam_paper(current_user):
    """上传试卷并进行OCR识别

    路由职责：
    1. 鉴权 (@login_required)
    2. 文件校验 (file_util)
    3. 调用 ocr_service 处理
    4. 保存结果到数据库
    5. 返回数据
    """

    # ===== 1. 文件校验 =====
    file = request.files.get('file')
    is_valid, error_msg = validate_image_file(file)
    if not is_valid:
        return fail(message=error_msg, code=400)

    # ===== 2. 保存文件 =====
    filepath = OCRBusinessService.save_uploaded_file(file, prefix='exam')

    # ===== 3. OCR 识别 + 分析报告 =====
    subject = request.form.get('subject', '数学')
    title = request.form.get('title', '未命名试卷')

    try:
        result = OCRBusinessService.process_ocr_upload(filepath, subject)
    except Exception as e:
        logger.exception('OCR 识别异常: %s', str(e))
        # 清理异常文件
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except OSError:
            pass
        return fail(message='OCR 识别失败，请检查图片是否清晰完整', code=500)

    ocr_text = result['ocr_text']
    analysis_report = result['analysis_report']

    # ===== 4. 保存到数据库 =====
    exam_paper = ExamPaper(
        user_id=current_user['user_id'],
        title=title,
        subject=subject,
        image_path=filepath,
        ocr_content=ocr_text,
        analysis_result=json.dumps(analysis_report, ensure_ascii=False),
        knowledge_points=json.dumps(analysis_report['knowledge_points'], ensure_ascii=False),
        mastery_level=json.dumps(analysis_report['mastery_level'], ensure_ascii=False),
    )
    db.session.add(exam_paper)

    # 更新用户知识点掌握度
    for kp, mastery in analysis_report['mastery_level'].items():
        existing = UserKnowledgeMastery.query.filter_by(
            user_id=current_user['user_id'],
            knowledge_point=kp,
        ).first()

        if existing:
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
                mastery_rate=mastery,
            )
            db.session.add(new_mastery)

    db.session.commit()

    # ===== 5. 返回数据 =====
    return success(data={
        'paper_id': exam_paper.id,
        'title': title,
        'subject': subject,
        'knowledge_points': analysis_report['knowledge_points'],
        'mastery_level': analysis_report['mastery_level'],
        'weak_points': analysis_report['weak_points'],
        'suggestions': analysis_report['suggestions'],
        'ocr_preview': (
            ocr_text[:500] + '...' if len(ocr_text) > 500 else ocr_text
        ),
    }, message='分析完成')
