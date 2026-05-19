# AI智能学习平台

一个集AI学情分析、智能刷题、错题本管理于一体的综合学习平台。

## 项目概述

本项目将两个AI学习系统完整合并，打造一个统一的智能学习平台：
- **AI学情分析系统**：试卷上传、OCR识别、知识点雷达图、薄弱点分析
- **AI智能刷题+错题本系统**：自动刷题、错题收录、正确率统计、学习时长统计、错题本管理

## 技术栈

### 后端
- Python 3.8+
- Flask 2.3.3
- MySQL 8.0+
- PaddleOCR 2.7.0.3
- JWT认证

### 前端
- Vue 3
- Element Plus
- ECharts 5
- Vite
- Pinia
- Axios

## 功能特性

### 🏠 首页数据看板 (Dashboard)
- 核心数据指标卡片：累计刷题总数、总体正确率、累计学习时长、待复习错题数量
- 每日刷题量趋势图表
- 正确率趋势图表
- 薄弱知识点TOP5展示
- 快捷功能入口

### 📊 AI学情分析
- 试卷图片上传（支持多格式）
- PaddleOCR智能识别试卷内容
- 自动提取知识点
- 知识点掌握度雷达图可视化
- 薄弱知识点自动识别标记
- 个性化学习建议生成
- 分析历史记录管理

### ✍️ 智能刷题
- 两种刷题模式：智能推荐 / 自定义选题
- 基于薄弱知识点智能推题
- 在线答题界面
- 实时自动判分与解析
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
- 修改密码
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

# 配置环境变量
# 编辑 .env 文件，修改数据库连接信息

# 启动服务
python server.py
```

后端服务将在 `http://localhost:5000` 启动

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

**测试账号：**
- 用户名：demo
- 密码：123456

## 项目结构

```
ai-learning-platform/
├── backend/                 # 后端项目
│   ├── app/
│   │   ├── api/            # API接口
│   │   ├── models/         # 数据模型
│   │   ├── services/       # 业务服务
│   │   └── utils/          # 工具类
│   ├── uploads/            # 上传文件目录
│   ├── requirements.txt    # Python依赖
│   ├── .env               # 环境配置
│   └── server.py         # 应用入口
├── frontend/               # 前端项目
│   ├── src/
│   │   ├── views/         # 页面组件
│   │   ├── components/    # 公共组件
│   │   ├── router/        # 路由配置
│   │   ├── store/         # 状态管理
│   │   ├── utils/         # 工具函数
│   │   └── api/           # API封装
│   ├── package.json
│   └── vite.config.js
├── sql/                    # 数据库脚本
│   └── init.sql
├── docs/                   # 文档目录
└── README.md
```

## API接口说明

### 认证模块 `/api/auth`
- `POST /register` - 用户注册
- `POST /login` - 用户登录
- `GET /user-info` - 获取用户信息
- `POST /update-profile` - 更新用户信息
- `POST /change-password` - 修改密码

### 学情分析 `/api/analysis`
- `POST /upload` - 上传试卷并分析
- `GET /history` - 获取分析历史
- `GET /detail/:id` - 获取分析详情
- `GET /knowledge-mastery` - 获取知识点掌握度
- `GET /weak-points` - 获取薄弱知识点

### 智能刷题 `/api/practice`
- `GET /questions` - 获取题目列表
- `GET /smart-recommend` - 智能推荐题目
- `POST /submit-answer` - 提交答案
- `GET /statistics` - 获取刷题统计
- `GET /daily-trend` - 获取每日趋势

### 错题本 `/api/wrong-question`
- `GET /list` - 获取错题列表
- `POST /review/:id` - 复习错题
- `POST /mark-mastered/:id` - 标记掌握
- `DELETE /remove/:id` - 删除错题
- `GET /statistics` - 获取统计
- `GET /review-today` - 今日待复习

### 首页看板 `/api/dashboard`
- `GET /overview` - 获取概览数据
- `GET /daily-trend` - 获取趋势数据
- `GET /weak-points` - 获取薄弱点
- `GET /recent-activity` - 最近活动

## 数据库表说明

| 表名 | 说明 |
|------|------|
| users | 用户表 |
| questions | 题库表 |
| knowledge_points | 知识点表 |
| study_records | 学习记录表 |
| exam_papers | 试卷分析表 |
| wrong_questions | 错题本表 |
| user_knowledge_mastery | 用户知识点掌握度表 |

## 开发说明

### 后端开发
- 遵循RESTful API设计规范
- 使用JWT进行身份认证
- 统一的响应格式：`{code, message, data}`

### 前端开发
- 使用Vue3 Composition API
- Element Plus UI组件库
- ECharts数据可视化
- Pinia状态管理

## 注意事项

1. **PaddleOCR安装**：首次运行会自动下载模型，可能需要较长时间
2. **数据库配置**：请确保MySQL服务已启动，并修改`.env`中的数据库配置
3. **端口占用**：确保5000（后端）和3000（前端）端口未被占用
4. **文件上传**：上传的试卷图片保存在`backend/uploads`目录

## License

MIT
