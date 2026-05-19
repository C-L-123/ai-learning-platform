-- AI智能学习平台数据库初始化脚本
-- 创建时间: 2024
-- 数据库: ai_learning_platform

-- 创建数据库
CREATE DATABASE IF NOT EXISTS ai_learning_platform DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE ai_learning_platform;

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL COMMENT '用户名',
    email VARCHAR(100) UNIQUE NOT NULL COMMENT '邮箱',
    password VARCHAR(255) NOT NULL COMMENT '密码(加密)',
    nickname VARCHAR(50) COMMENT '昵称',
    avatar VARCHAR(255) COMMENT '头像',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- 题目表
CREATE TABLE IF NOT EXISTS questions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    subject VARCHAR(50) NOT NULL COMMENT '科目',
    knowledge_point VARCHAR(100) NOT NULL COMMENT '知识点',
    difficulty INT DEFAULT 1 COMMENT '难度:1-简单,2-中等,3-困难',
    question_type VARCHAR(20) COMMENT '题型',
    content TEXT NOT NULL COMMENT '题目内容',
    options TEXT COMMENT '选项(JSON)',
    answer TEXT NOT NULL COMMENT '答案',
    analysis TEXT COMMENT '解析',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='题目表';

-- 知识点表
CREATE TABLE IF NOT EXISTS knowledge_points (
    id INT PRIMARY KEY AUTO_INCREMENT,
    subject VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    parent_id INT,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES knowledge_points(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='知识点表';

-- 学习记录表
CREATE TABLE IF NOT EXISTS study_records (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    question_id INT,
    study_type VARCHAR(20) NOT NULL COMMENT '学习类型:practice/exam/review',
    is_correct BOOLEAN COMMENT '是否正确',
    answer_time INT COMMENT '答题时间(秒)',
    study_date DATE DEFAULT (CURRENT_DATE),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (question_id) REFERENCES questions(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学习记录表';

-- 试卷表
CREATE TABLE IF NOT EXISTS exam_papers (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    title VARCHAR(200) COMMENT '试卷标题',
    subject VARCHAR(50) COMMENT '科目',
    image_path VARCHAR(255) COMMENT '图片路径',
    ocr_content TEXT COMMENT 'OCR识别内容',
    analysis_result TEXT COMMENT '分析结果(JSON)',
    knowledge_points TEXT COMMENT '知识点列表(JSON)',
    mastery_level TEXT COMMENT '掌握度(JSON)',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='试卷表';

-- 错题本表
CREATE TABLE IF NOT EXISTS wrong_questions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    question_id INT NOT NULL,
    wrong_answer TEXT COMMENT '错误答案',
    wrong_count INT DEFAULT 1 COMMENT '错误次数',
    status VARCHAR(20) DEFAULT 'pending' COMMENT '状态:pending待复习,mastered已掌握',
    last_review_at DATETIME COMMENT '上次复习时间',
    next_review_at DATETIME COMMENT '下次复习时间',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (question_id) REFERENCES questions(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='错题本表';

-- 用户知识点掌握度表
CREATE TABLE IF NOT EXISTS user_knowledge_mastery (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    knowledge_point VARCHAR(100) NOT NULL,
    subject VARCHAR(50),
    total_questions INT DEFAULT 0,
    correct_questions INT DEFAULT 0,
    mastery_rate FLOAT DEFAULT 0.0 COMMENT '掌握率0-100',
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY _user_knowledge_uc (user_id, knowledge_point)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户知识点掌握度表';

-- 插入基础题库数据 - 数学
INSERT INTO questions (subject, knowledge_point, difficulty, question_type, content, options, answer, analysis) VALUES
('数学', '函数', 1, '单选', '函数f(x)=x²在x=2处的导数是多少？', '["2", "4", "6", "8"]', '4', '根据导数公式，f\'(x)=2x，所以f\'(2)=4'),
('数学', '函数', 1, '单选', '下列哪个是奇函数？', '["y=x²", "y=x³", "y=|x|", "y=e^x"]', 'y=x³', '奇函数满足f(-x) = -f(x)，y=x³满足此条件'),
('数学', '导数', 2, '单选', '函数f(x)=x³-3x的极大值点是？', '["x=-1", "x=0", "x=1", "x=2"]', 'x=-1', '求导得f\'(x)=3x²-3，令f\'(x)=0得x=±1，x=-1时为极大值点'),
('数学', '导数', 1, '单选', '函数y=sinx的导数是？', '["cosx", "-cosx", "sinx", "-sinx"]', 'cosx', '基本导数公式：(sinx)\' = cosx'),
('数学', '数列', 2, '单选', '等差数列{aₙ}中，a₁=1，d=2，则a₁₀=？', '["17", "19", "21", "23"]', '19', 'aₙ = a₁ + (n-1)d = 1 + 9×2 = 19'),
('数学', '数列', 1, '单选', '等比数列1,2,4,8,...的公比是？', '["1", "2", "3", "4"]', '2', '公比q = 2/1 = 4/2 = 2'),
('数学', '三角函数', 1, '单选', 'sin30°的值是？', '["1/2", "√2/2", "√3/2", "1"]', '1/2', '特殊角三角函数值：sin30° = 1/2'),
('数学', '三角函数', 2, '单选', 'sin²x + cos²x = ?', '["0", "1", "2", "tanx"]', '1', '三角恒等式：sin²x + cos²x = 1'),
('数学', '立体几何', 2, '单选', '正方体的棱长为a，则其体对角线长为？', '["a", "a√2", "a√3", "2a"]', 'a√3', '体对角线 = √(a²+a²+a²) = a√3'),
('数学', '解析几何', 2, '单选', '圆x²+y²=4的半径是？', '["1", "2", "4", "16"]', '2', '标准方程x²+y²=r²，所以r=2'),
('数学', '概率', 1, '单选', '抛一枚硬币，正面朝上的概率是？', '["1/4", "1/3", "1/2", "1"]', '1/2', '古典概型，两种等可能结果'),
('数学', '概率', 2, '单选', '从1-5中任取两个数，和为偶数的概率是？', '["1/5", "2/5", "3/5", "4/5"]', '2/5', 'C(5,2)=10种，和为偶数需同奇偶，C(3,2)+C(2,2)=4种，概率4/10=2/5'),
('数学', '不等式', 2, '单选', '不等式x²-3x+2<0的解集是？', '["x<1", "1<x<2", "x>2", "x<1或x>2"]', '1<x<2', '因式分解(x-1)(x-2)<0，解集为1<x<2'),
('数学', '向量', 1, '单选', '向量(1,2)和(2,1)的数量积是？', '["2", "3", "4", "5"]', '4', '数量积 = 1×2 + 2×1 = 4'),
('数学', '积分', 2, '单选', '∫x dx = ?', '["x", "x²/2 + C", "x² + C", "2x"]', 'x²/2 + C', '积分公式：∫xⁿdx = xⁿ⁺¹/(n+1) + C');

-- 插入英语题目
INSERT INTO questions (subject, knowledge_point, difficulty, question_type, content, options, answer, analysis) VALUES
('英语', '语法', 1, '单选', 'He ___ to school every day.', '["go", "goes", "going", "went"]', 'goes', '一般现在时，第三人称单数动词加s'),
('英语', '语法', 2, '单选', 'If I ___ you, I would study harder.', '["am", "was", "were", "be"]', 'were', '虚拟语气，与现在事实相反用were'),
('英语', '词汇', 1, '单选', 'The opposite of "big" is ___.', '["small", "tall", "long", "old"]', 'small', 'big的反义词是small'),
('英语', '时态', 2, '单选', 'She ___ English for 5 years.', '["studies", "studied", "has studied", "is studying"]', 'has studied', 'for+时间段用现在完成时'),
('英语', '从句', 2, '单选', 'This is the book ___ I bought yesterday.', '["who", "whom", "which", "whose"]', 'which', '定语从句，先行词是物用which');

-- 插入物理题目
INSERT INTO questions (subject, knowledge_point, difficulty, question_type, content, options, answer, analysis) VALUES
('物理', '力学', 1, '单选', 'F=ma是哪个定律的表达式？', '["牛顿第一定律", "牛顿第二定律", "牛顿第三定律", "万有引力定律"]', '牛顿第二定律', '牛顿第二定律：F=ma'),
('物理', '运动学', 1, '单选', '匀速直线运动的速度公式是？', '["v=s/t", "v=at", "v=v₀+at", "v²=2as"]', 'v=s/t', '速度=路程/时间'),
('物理', '能量守恒', 2, '单选', '动能的表达式是？', '["mgh", "mv", "½mv²", "mv²"]', '½mv²', '动能Eₖ = ½mv²'),
('物理', '电场', 2, '单选', '电场强度的单位是？', '["N", "C", "N/C", "J"]', 'N/C', 'E=F/q，单位N/C'),
('物理', '电路', 1, '单选', '欧姆定律的表达式是？', '["U=IR", "P=UI", "W=UIt", "Q=I²Rt"]', 'U=IR', '欧姆定律：U=IR');

-- 创建索引优化查询
CREATE INDEX idx_study_records_user ON study_records(user_id);
CREATE INDEX idx_study_records_date ON study_records(study_date);
CREATE INDEX idx_wrong_questions_user ON wrong_questions(user_id);
CREATE INDEX idx_wrong_questions_status ON wrong_questions(status);
CREATE INDEX idx_exam_papers_user ON exam_papers(user_id);
CREATE INDEX idx_questions_subject ON questions(subject);
CREATE INDEX idx_questions_knowledge ON questions(knowledge_point);
CREATE INDEX idx_mastery_user ON user_knowledge_mastery(user_id);

-- 插入默认测试用户（密码：123456）
-- 密码已使用bcrypt加密
INSERT INTO users (username, email, password, nickname) VALUES 
('demo', 'demo@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewYGyJQqHhKxPFwW', '演示用户');
