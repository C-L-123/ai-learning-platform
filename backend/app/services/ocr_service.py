"""
OCR 业务服务层
封装：图片保存、PaddleOCR 识别、文本提取、学情分析报告生成
全局仅初始化一次 OCR 模型（单例），避免重复加载卡顿
所有识别操作均有日志记录
"""

import os
import json
import uuid
import time
import logging
from flask import current_app
from werkzeug.utils import secure_filename

from app.models import Subject
from app.utils.logger_util import log_ocr_action

logger = logging.getLogger(__name__)


class OCRBusinessService:
    """OCR 业务服务"""

    _ocr_instance = None

    @classmethod
    def _get_ocr_engine(cls):
        """全局单例获取 PaddleOCR 实例（避免重复加载）"""
        if cls._ocr_instance is None:
            try:
                from app.utils.ocr_service import OCRService
                cls._ocr_instance = OCRService()
                logger.info('[OCR] PaddleOCR 模型初始化成功（全局单例）')
                log_ocr_action('init', 'PaddleOCR', True)
            except Exception as e:
                log_ocr_action('init', 'PaddleOCR', False, error=str(e))
                raise
        return cls._ocr_instance

    @staticmethod
    def save_uploaded_file(file_obj, prefix='exam'):
        """保存上传文件到指定目录

        Args:
            file_obj: Flask request.files 中的文件对象
            prefix: 文件名前缀，默认 'exam'

        Returns:
            str: 保存后的完整文件路径
        """
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        filename = secure_filename(f"{prefix}_{uuid.uuid4().hex}_{file_obj.filename}")
        filepath = os.path.join(upload_folder, filename)
        file_obj.save(filepath)
        return filepath

    @classmethod
    def process_ocr_upload(cls, filepath, subject='数学'):
        """执行 OCR 识别并生成学情分析报告

        完整流程：
        1. PaddleOCR 识别图片文字
        2. 从数据库读取该科目的关键词配置
        3. 提取知识点、计算掌握度、生成分析报告

        Args:
            filepath: 图片文件的完整路径
            subject: 科目名称

        Returns:
            dict: {ocr_text, analysis_report}

        Raises:
            Exception: OCR 识别失败时抛出
        """
        log_ocr_action('start', filepath, user_info=f'科目={subject}')
        start_time = time.time()

        try:
            service = cls._get_ocr_engine()

            # 1. PaddleOCR 识别图片
            ocr_text = service.recognize_image(filepath)

            # 2. 从数据库读取该科目配置的关键词
            subject_record = Subject.query.filter_by(name=subject, is_active=True).first()
            keywords = (
                json.loads(subject_record.keywords)
                if subject_record and subject_record.keywords
                else None
            )

            # 3. 生成分析报告（知识点 + 掌握度 + 建议）
            analysis_report = service.generate_analysis_report(ocr_text, subject, keywords)

            elapsed = round(time.time() - start_time, 2)
            log_ocr_action(
                'success', filepath,
                extra={
                    'text_length': len(ocr_text),
                    'knowledge_points': analysis_report.get('knowledge_points', []),
                    'elapsed': elapsed,
                }
            )

            return {
                'ocr_text': ocr_text,
                'analysis_report': analysis_report,
            }

        except Exception as e:
            elapsed = round(time.time() - start_time, 2)
            log_ocr_action('error', filepath, extra={'elapsed': elapsed}, error=str(e))
            raise
