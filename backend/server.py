import os
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 导入模型和路由
from app.models import db
from app.api import auth, analysis, practice, wrong_question, dashboard

def create_app():
    app = Flask(__name__)
    
    # 配置
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key')
    app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))
    
    # 数据库配置
    mysql_host = os.getenv('MYSQL_HOST', 'localhost')
    mysql_port = os.getenv('MYSQL_PORT', '3306')
    mysql_user = os.getenv('MYSQL_USER', 'root')
    mysql_password = os.getenv('MYSQL_PASSWORD', '123456')
    mysql_database = os.getenv('MYSQL_DATABASE', 'ai_learning_platform')
    
    app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_database}?charset=utf8mb4'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 初始化扩展
    CORS(app)
    db.init_app(app)
    
    # 注册蓝图
    app.register_blueprint(auth.bp, url_prefix='/api/auth')
    app.register_blueprint(analysis.bp, url_prefix='/api/analysis')
    app.register_blueprint(practice.bp, url_prefix='/api/practice')
    app.register_blueprint(wrong_question.bp, url_prefix='/api/wrong-question')
    app.register_blueprint(dashboard.bp, url_prefix='/api/dashboard')
    
    # 创建上传目录
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # 健康检查
    @app.route('/api/health')
    def health_check():
        return jsonify({'code': 200, 'message': 'AI智能学习平台服务运行正常', 'data': None})
    
    return app

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
