# AI智能学习平台

一个集AI学情分析、智能刷题、错题本管理于一体的综合学习平台。

## 项目概述

本项目将两个AI学习系统完整合并，打造一个统一的智能学习平台：
- **AI学情分析系统**：试卷上传、OCR识别、知识点雷达图、薄弱点分析
- **AI智能刷题+错题本系统**：AI 出题（DeepSeek）、自动判分、错题收录、正确率统计、学习时长统计、错题本管理

## 技术栈

### 后端
- Python 3.8+
- Flask 2.3.3
- Flask-CORS / Flask-SQLAlchemy
- MySQL 8.0+
- PaddleOCR 2.7.0.3（试卷 OCR 识别）
- DeepSeek API（AI 出题、AI 判分、AI 学情报告）
- PyJWT — JWT 鉴权（`@login_required` 装饰器）
- bcrypt — 密码加盐加密

### 前端
- Vue 3
- Element Plus
- ECharts 5
- Vite
- Pinia
- Axios

## 架构设计

```
路由层 (api/)      → 鉴权 / 参数校验 / 返回响应（不含业务逻辑）
   ↓
服务层 (services/)  → OCR 识别 / LLM 调用 / 学情统计 / 日志记录
   ↓
工具层 (utils/)     → PaddleOCR 引擎 / AI 客户端 / JWT 加密 / 密码加密 / 文件校验
```

### 三层分离

| 层级 | 目录 | 职责 |
|------|------|------|
| 路由层 | `app/api/` | `@login_required` 鉴权、`file_util` 文件校验、调用 service、`success()/fail()` 返回 |
| 服务层 | `app/services/` | 业务逻辑：`ocr_service`（OCR 识别+报告）、`llm_service`（AI 出题+判分）、`stat_service`（统计计算） |
| 工具层 | `app/utils/` | 基础能力：`jwt_util`（JWT 加解密）、`pwd_util`（bcrypt 密码）、`file_util`（文件校验）、`response_util`（统一响应）、`logger_util`（结构化日志） |

## 功能特性

### 🏠 首页数据看板 (Dashboard)
- 核心数据指标卡片：累计刷题总数、总体正确率、累计学习时长、待复习错题数量
- 每日刷题量趋势图表
- 正确率趋势图表
- 薄弱知识点TOP5展示
- 快捷功能入口

### 📊 AI学情分析
- 试卷图片上传（支持 png/jpg/jpeg/gif/bmp 格式，大小限制 16MB）
- PaddleOCR智能识别试卷内容
- 自动提取知识点
- 知识点掌握度雷达图可视化
- 薄弱知识点自动识别标记
- 个性化学习建议生成
- 分析历史记录管理（查看详情、删除）

### ✍️ 智能刷题
- 两种刷题模式：**智能推荐**（基于薄弱知识点） / **自定义选题**（按科目/难度/题型）
- DeepSeek AI 自动出题
- 在线答题界面
- 选择题自动判分 / 解答题 AI 判分
- 实时正确率统计
- 学习时长计时

### 📚 错题本
- 错题自动收录
- 分类管理：待复习 / 已掌握
- 错题重做功能
- 知识点标签关联
- 错误次数统计
- 批量标记掌握

### 👤 个人中心
- 用户信息管理
- 修改密码（bcrypt 加盐验证）
- 学习记录总览
- 学习数据统计

### 🔄 数据闭环
- 学情分析识别出薄弱知识点 → 自动推送对应题目
- 用户刷题数据（正确率、错题）实时反馈更新学情分析结果
- 形成完整的"分析-刷题-再分析"学习闭环

## 快速开始

### 环境要求
- Python 3.8+
- Node.js 16+
- MySQL 8.0+

### 1. 数据库初始化

```bash
# 登录MySQL
mysql -u root -p

# 执行初始化脚本
source sql/init.sql
```

### 2. 后端启动

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 配置环境变量（编辑 .env 文件，修改数据库连接信息）
cp .env.example .env
# 修改 .env 中以下配置：
#   MYSQL_HOST / MYSQL_PORT / MYSQL_USER / MYSQL_PASSWORD / MYSQL_DATABASE
#   DEEPSEEK_API_KEY（AI 出题必需）
#   SECRET_KEY / JWT_SECRET_KEY

# 启动服务
python server.py
```

后端服务将在 `http://localhost:5000` 启动

> **首次启动**：PaddleOCR 会自动下载识别模型，可能需要几分钟。OCR 模型以全局单例加载，后续请求无需重新加载。

### 3. 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务
npm run dev
```

前端服务将在 `http://localhost:3000` 启动

### 4. 访问系统

打开浏览器访问 `http://localhost:3000`

## 项目结构

```
ai-learning-platform/
├── backend/                    # 后端项目
│   ├── app/
│   │   ├── api/               # API 路由层（仅鉴权+校验+返回）
│   │   │   ├── auth.py        #   认证（登录/注册/用户信息）
│   │   │   ├── ocr.py         #   OCR 上传（试卷识别）
│   │   │   ├── analysis.py    #   学情分析（历史/详情/报告/薄弱点）
│   │   │   ├── practice.py    #   智能刷题（出题/判分/统计）
│   │   │   ├── wrong_question.py  # 错题本
│   │   │   ├── dashboard.py   #   首页看板
│   │   │   └── subject.py     #   科目管理
│   │   ├── models/            # 数据模型（8 张表）
│   │   │   └── __init__.py    #   User / Question / StudyRecord / ExamPaper / WrongQuestion / ...
│   │   ├── services/          # 业务服务层（核心逻辑）
│   │   │   ├── ocr_service.py #   OCR 识别 + 学情分析（PaddleOCR 单例）
│   │   │   ├── llm_service.py #   AI 出题 + 判分 + 学习报告（DeepSeek 单例）
│   │   │   └── stat_service.py    #  学情统计计算
│   │   └── utils/             # 工具层
│   │       ├── jwt_util.py    #   JWT 生成 + @login_required 鉴权装饰器
│   │       ├── pwd_util.py    #   bcrypt 加盐密码加密/校验
│   │       ├── file_util.py   #   文件后缀+大小校验
│   │       ├── response_util.py   #  统一 success()/fail() 响应
│   │       ├── logger_util.py     #   结构化日志（OCR/AI/登录）
│   │       ├── ocr_service.py     #   PaddleOCR 引擎封装
│   │       └── ai_question_service.py  # DeepSeek API 客户端
│   ├── logs/                  # 日志文件（按天轮转，保留30天）
│   ├── uploads/               # 上传文件目录
│   ├── config.py              # 集中配置（数据库/JWT/上传/AI/OCR）
│   ├── server.py              # 应用入口（全局异常捕获）
│   ├── requirements.txt       # Python 依赖
│   └── .env                   # 环境变量（数据库账号等敏感信息）
├── frontend/                  # 前端项目
│   ├── src/
│   │   ├── views/             # 页面组件
│   │   ├── router/            # 路由配置
│   │   ├── store/             # Pinia 状态管理
│   │   └── utils/             # 工具函数（request封装 / LaTeX渲染）
│   ├── package.json
│   └── vite.config.js
├── sql/                       # 数据库脚本
│   └── init.sql
└── README.md
```

## 配置说明

所有敏感配置集中在 `backend/config.py`，从 `.env` 环境变量读取：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `SECRET_KEY` | Flask 密钥 | - |
| `JWT_SECRET_KEY` | JWT 签名密钥 | - |
| `JWT_EXPIRATION_DAYS` | Token 有效期（天） | 7 |
| `MYSQL_HOST` | 数据库地址 | localhost |
| `MYSQL_PORT` | 数据库端口 | 3306 |
| `MYSQL_USER` | 数据库用户 | root |
| `MYSQL_PASSWORD` | 数据库密码 | - |
| `MYSQL_DATABASE` | 数据库名 | ai_learning_platform |
| `UPLOAD_FOLDER` | 上传文件目录 | uploads |
| `MAX_CONTENT_LENGTH` | 文件大小上限（字节） | 16MB |
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 | - |
| `DEEPSEEK_BASE_URL` | DeepSeek API 地址 | https://api.deepseek.com |
| `DEEPSEEK_MODEL` | DeepSeek 模型 | deepseek-chat |

## API接口说明

> 所有需登录的接口统一使用 `@login_required` 鉴权（请求头 `Authorization: Bearer <token>`）。
> 所有接口统一响应格式：`{ code: int, message: str, data: any }`。

### 认证模块 `/api/auth`
| 方法 | 路径 | 说明 | 鉴权 |
|------|------|------|------|
| POST | `/register` | 用户注册 | 否 |
| POST | `/login` | 用户登录，返回 JWT token | 否 |
| GET | `/user-info` | 获取当前用户信息 | 是 |
| POST | `/update-profile` | 更新用户资料 | 是 |
| POST | `/change-password` | 修改密码（需验证旧密码） | 是 |

### 学情分析 `/api/analysis`
| 方法 | 路径 | 说明 | 鉴权 |
|------|------|------|------|
| POST | `/upload` | 上传试卷图片，OCR 识别并生成分析报告 | 是 |
| GET | `/history` | 获取分析历史记录（分页） | 是 |
| GET | `/detail/<id>` | 获取分析详情 | 是 |
| DELETE | `/delete/<id>` | 删除分析记录及图片文件 | 是 |
| GET | `/knowledge-mastery` | 知识点掌握度（雷达图） | 是 |
| GET | `/ai-report` | AI 生成个性化学习报告 | 是 |
| GET | `/weak-points` | 薄弱知识点列表 | 是 |

### 智能刷题 `/api/practice`
| 方法 | 路径 | 说明 | 鉴权 |
|------|------|------|------|
| GET | `/questions` | AI 生成题目（支持按科目/难度/题型筛选） | 是 |
| GET | `/smart-recommend` | 基于薄弱知识点智能推荐题目 | 是 |
| POST | `/submit-answer` | 提交答案并判分（解答题 AI 判分） | 是 |
| GET | `/statistics` | 刷题统计数据 | 是 |
| POST | `/session-complete` | 记录一次刷题会话的总时长 | 是 |
| GET | `/daily-trend` | 近7天每日刷题趋势 | 是 |
| POST | `/upload-image` | 上传解答题手写作答图片 | 是 |

### 错题本 `/api/wrong-question`
| 方法 | 路径 | 说明 | 鉴权 |
|------|------|------|------|
| GET | `/list` | 错题列表（可按状态/科目筛选，分页） | 是 |
| POST | `/review/<id>` | 复习错题并提交结果 | 是 |
| POST | `/mark-mastered/<id>` | 标记为已掌握 | 是 |
| DELETE | `/remove/<id>` | 从错题本移除 | 是 |
| GET | `/statistics` | 错题统计（按科目分布） | 是 |
| GET | `/review-today` | 今日待复习错题列表 | 是 |

### 首页看板 `/api/dashboard`
| 方法 | 路径 | 说明 | 鉴权 |
|------|------|------|------|
| GET | `/overview` | 首页概览数据（统计卡片+今日数据） | 是 |
| GET | `/daily-trend` | 近7天刷题趋势 | 是 |
| GET | `/weak-points` | 薄弱知识点 TOP5 | 是 |
| GET | `/recent-activity` | 最近 10 条学习活动 | 是 |

### 科目管理 `/api/subject`
| 方法 | 路径 | 说明 | 鉴权 |
|------|------|------|------|
| GET | `/list` | 获取所有启用科目（无需登录） | 否 |
| GET | `/all` | 获取全部科目（管理用） | 是 |
| POST | `/add` | 新增科目 | 是 |
| POST | `/update/<id>` | 更新科目（名称/关键词/启用状态） | 是 |
| DELETE | `/delete/<id>` | 删除科目 | 是 |

## 数据库表说明

| 表名 | 说明 |
|------|------|
| users | 用户表（bcrypt 加密密码） |
| subjects | 科目表（名称 + 知识点关键词JSON） |
| questions | 题库表（AI 生成） |
| knowledge_points | 知识点表 |
| study_records | 学习记录表（练习/复习/会话时长） |
| exam_papers | 试卷分析表（OCR 内容 + 分析报告JSON） |
| wrong_questions | 错题本表（错误次数/状态/复习时间） |
| user_knowledge_mastery | 用户知识点掌握度表 |

## 日志系统

项目启动时自动初始化日志系统，输出到 `backend/logs/` 目录：

- **文件轮转**：按天轮转，保留 30 天
- **业务日志**：
  - `[AUTH]` — 用户登录/注册行为（成功/失败 + IP）
  - `[OCR]` — PaddleOCR 识别（启动/识别/错误 + 耗时）
  - `[AI]` — DeepSeek 大模型调用（出题/判分/报告 + 耗时）
- **双输出**：控制台实时查看 + 文件持久化存储

## 开发说明

### 后端开发
- 遵循 RESTful API 设计规范
- 使用 `@login_required` 装饰器进行 JWT 鉴权
- 使用 `success()` / `fail()` 统一响应格式
- 路由层不写业务逻辑，所有逻辑在 `services/` 层
- OCR 和 LLM 使用单例模式，全局仅初始化一次
- `config.py` 集中管理所有配置项，禁止在代码中硬编码

### 前端开发
- 使用 Vue3 Composition API
- Element Plus UI 组件库
- ECharts 数据可视化
- Pinia 状态管理
- Axios 请求封装（统一 token 注入 + 错误处理）

## 注意事项

1. **PaddleOCR 安装**：首次运行会自动下载模型，可能需要较长时间
2. **DeepSeek API**：AI 出题功能需要有效的 `DEEPSEEK_API_KEY`，请在 `.env` 中配置
3. **数据库配置**：请确保 MySQL 服务已启动，并修改 `.env` 中的数据库配置
4. **端口占用**：确保 5000（后端）和 3000（前端）端口未被占用
5. **文件上传**：上传的试卷图片保存在 `backend/uploads` 目录，大小限制 16MB
6. **日志查看**：运行日志在 `backend/logs/app.log`，按天轮转保留 30 天

## License

MIT
