"""
应用配置模块
将代码中写死的数据库账号、上传路径、JWT 密钥、OCR 路径等集中管理
所有配置项从 .env 环境变量读取，未配置时使用默认值
"""

import os
from dotenv import load_dotenv

# 加载 .env 环境变量
load_dotenv()


class Config:
    """应用配置"""

    # ========== Flask 基础配置 ==========
    SECRET_KEY = os.getenv('SECRET_KEY', 'ai-learning-platform-secret-key-2024')

    # ========== JWT 配置 ==========
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'ai-learning-jwt-secret-key-2024')
    JWT_EXPIRATION_DAYS = int(os.getenv('JWT_EXPIRATION_DAYS', 7))
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_PREFIX = 'Bearer '

    # ========== 数据库配置 ==========
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_PORT = os.getenv('MYSQL_PORT', '3306')
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '123456')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'ai_learning_platform')

    @staticmethod
    def get_database_uri():
        """获取数据库连接 URI"""
        return (
            f'mysql+pymysql://{Config.MYSQL_USER}:{Config.MYSQL_PASSWORD}'
            f'@{Config.MYSQL_HOST}:{Config.MYSQL_PORT}/{Config.MYSQL_DATABASE}'
            f'?charset=utf8mb4'
        )

    # ========== 文件上传配置 ==========
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

    # ========== DeepSeek AI 配置 ==========
    DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')
    DEEPSEEK_BASE_URL = os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
    DEEPSEEK_MODEL = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')

    # ========== OCR 配置 ==========
    OCR_LANG = os.getenv('OCR_LANG', 'ch')
    OCR_USE_DOC_ORIENTATION = True
    OCR_CONFIDENCE_THRESHOLD = float(os.getenv('OCR_CONFIDENCE_THRESHOLD', 0.9))
