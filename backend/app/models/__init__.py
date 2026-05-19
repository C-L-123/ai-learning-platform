from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    """用户模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    nickname = db.Column(db.String(50))
    avatar = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关联关系
    study_records = db.relationship('StudyRecord', backref='user', lazy=True)
    exam_papers = db.relationship('ExamPaper', backref='user', lazy=True)
    wrong_questions = db.relationship('WrongQuestion', backref='user', lazy=True)

class Question(db.Model):
    """题目模型"""
    __tablename__ = 'questions'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    subject = db.Column(db.String(50), nullable=False)  # 科目：数学、英语、物理等
    knowledge_point = db.Column(db.String(100), nullable=False)  # 知识点
    difficulty = db.Column(db.Integer, default=1)  # 难度：1-简单，2-中等，3-困难
    question_type = db.Column(db.String(20))  # 题型：单选、多选、填空、解答
    content = db.Column(db.Text, nullable=False)  # 题目内容
    options = db.Column(db.Text)  # 选项（JSON格式）
    answer = db.Column(db.Text, nullable=False)  # 答案
    analysis = db.Column(db.Text)  # 解析
    created_at = db.Column(db.DateTime, default=datetime.now)

class KnowledgePoint(db.Model):
    """知识点模型"""
    __tablename__ = 'knowledge_points'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    subject = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('knowledge_points.id'))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)

class StudyRecord(db.Model):
    """学习记录模型"""
    __tablename__ = 'study_records'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'))
    study_type = db.Column(db.String(20), nullable=False)  # practice, exam, review
    is_correct = db.Column(db.Boolean)
    answer_time = db.Column(db.Integer)  # 答题时间（秒）
    study_date = db.Column(db.Date, default=datetime.now().date)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    question = db.relationship('Question', backref='study_records')

class ExamPaper(db.Model):
    """试卷模型"""
    __tablename__ = 'exam_papers'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200))
    subject = db.Column(db.String(50))
    image_path = db.Column(db.String(255))
    ocr_content = db.Column(db.Text)
    analysis_result = db.Column(db.Text)  # JSON格式的分析结果
    knowledge_points = db.Column(db.Text)  # JSON格式的知识点
    mastery_level = db.Column(db.Text)  # JSON格式的掌握度
    created_at = db.Column(db.DateTime, default=datetime.now)

class WrongQuestion(db.Model):
    """错题本模型"""
    __tablename__ = 'wrong_questions'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    wrong_answer = db.Column(db.Text)
    wrong_count = db.Column(db.Integer, default=1)
    status = db.Column(db.String(20), default='pending')  # pending:待复习, mastered:已掌握
    last_review_at = db.Column(db.DateTime)
    next_review_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    question = db.relationship('Question', backref='wrong_questions')

class UserKnowledgeMastery(db.Model):
    """用户知识点掌握度模型"""
    __tablename__ = 'user_knowledge_mastery'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, nullable=False)
    knowledge_point = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(50))
    total_questions = db.Column(db.Integer, default=0)
    correct_questions = db.Column(db.Integer, default=0)
    mastery_rate = db.Column(db.Float, default=0.0)  # 掌握率 0-100
    last_updated = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'knowledge_point', name='_user_knowledge_uc'),
    )
