"""
AI 智能学习平台 - 服务入口
负责 Flask 应用初始化、蓝图注册、全局异常捕获、日志系统配置
"""

import os
import logging
from flask import Flask
from flask_cors import CORS

from config import Config
from app.models import db
from app.api import auth, analysis, ocr, practice, wrong_question, dashboard, subject
from app.utils.response_util import success, fail
from app.utils.logger_util import setup_logging

logger = logging.getLogger(__name__)


def create_app():
    app = Flask(__name__)

    # ========== 日志系统 ==========
    setup_logging(log_dir='logs')

    # ========== 应用配置（从 config.py 集中读取）==========
    app.config['SECRET_KEY'] = Config.SECRET_KEY
    app.config['JWT_SECRET_KEY'] = Config.JWT_SECRET_KEY
    app.config['UPLOAD_FOLDER'] = Config.UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH
    app.config['SQLALCHEMY_DATABASE_URI'] = Config.get_database_uri()
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # ========== 初始化扩展 ==========
    CORS(app)
    db.init_app(app)

    # ========== 注册蓝图 ==========
    app.register_blueprint(auth.bp, url_prefix='/api/auth')
    app.register_blueprint(ocr.bp, url_prefix='/api/analysis')        # OCR 上传（拆分后的新蓝图）
    app.register_blueprint(analysis.bp, url_prefix='/api/analysis')   # 学情分析（历史记录等）
    app.register_blueprint(practice.bp, url_prefix='/api/practice')
    app.register_blueprint(wrong_question.bp, url_prefix='/api/wrong-question')
    app.register_blueprint(dashboard.bp, url_prefix='/api/dashboard')
    app.register_blueprint(subject.bp, url_prefix='/api/subject')

    # ========== 创建上传目录 ==========
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # ========== 全局异常捕获 ==========

    @app.errorhandler(Exception)
    def handle_exception(e):
        """捕获所有未处理的异常，统一返回错误信息（不爆堆栈）"""
        code = getattr(e, 'code', 500)
        if isinstance(code, int) and 400 <= code < 500:
            return fail(message=f'请求错误: {code}', code=code)

        logger.exception('服务器内部错误: %s', str(e))
        return fail(message='服务器内部错误，请稍后重试', code=500)

    @app.errorhandler(404)
    def handle_404(e):
        return fail(message='接口不存在', code=404)

    @app.errorhandler(405)
    def handle_405(e):
        return fail(message='请求方法不允许', code=405)

    @app.errorhandler(413)
    def handle_413(e):
        max_mb = Config.MAX_CONTENT_LENGTH // (1024 * 1024)
        return fail(message=f'文件大小超过限制（最大 {max_mb}MB）', code=413)

    # ========== 路由 ==========

    @app.route('/api/health')
    def health_check():
        return success(message='AI智能学习平台服务运行正常')

    return app


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
