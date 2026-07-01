import os
import json
import re
from dotenv import load_dotenv
from openai import OpenAI

# 显式加载 .env，防止 Flask debug 重启后环境变量丢失
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))


class AIQuestionService:
    """使用 DeepSeek API 生成题目的服务"""

    def __init__(self):
        api_key = os.getenv('DEEPSEEK_API_KEY')
        if not api_key:
            raise ValueError('未配置 DEEPSEEK_API_KEY，请在 backend/.env 中设置')

        self.client = OpenAI(
            api_key=api_key,
            base_url=os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
        )
        self.model = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')
        print(f'[AI] DeepSeek 服务初始化成功, model={self.model}')

    def generate_questions(self, subject, knowledge_point=None, difficulty=1, count=5, question_type=None):
        """调用 AI 生成指定科目的题目

        Args:
            subject: 科目名称，如 数学、英语、物理
            knowledge_point: 知识点（可选）
            difficulty: 难度 1-简单 2-中等 3-困难
            count: 生成数量

        Returns:
            list[dict] 题目列表，每项包含 content/options/answer/analysis/knowledge_point/difficulty
        """
        difficulty_map = {1: '简单（基础）', 2: '中等', 3: '困难'}
        diff_label = difficulty_map.get(difficulty, '难度混合（简单、中等、困难各占一定比例）')

        kp_hint = f'，知识点为「{knowledge_point}」' if knowledge_point else ''

        if question_type == '解答':
            type_hint = '全部为解答题'
            type_rule = '- 全部为解答题：answer为参考答案（简明扼要），options留空数组，question_type为"解答"'
        elif question_type == '单选':
            type_hint = '全部为单选题'
            type_rule = '- 全部为单选题：必须有4个选项（A/B/C/D），answer为选项字母，question_type为"单选"'
        else:
            type_hint = '包含单选题和解答题（约各占一半）'
            type_rule = '- 单选题：必须有4个选项（A/B/C/D），answer为选项字母，question_type为"单选"\n- 解答题：answer为参考答案（简明扼要），options留空数组，question_type为"解答"'

        diff_rule = '' if difficulty else '- 每道题的difficulty字段：简单题为1，中等题为2，困难题为3，三种难度都要有'

        prompt = f"""你是一位专业的{subject}学科出题老师。请生成 {count} 道{subject}科目的题目。

要求：
- 难度：{diff_label}{kp_hint}
{diff_rule}
- 题型：{type_hint}
- {type_rule}
- 题目内容要准确、科学，不能有知识性错误
- 解析必须详细且有教学价值，具体要求：
  - 对于选择题：先说明正确答案的原因，再逐个分析其他选项为什么错
  - 对于解答题：给出完整的解题步骤和思路
  - 解析要帮助学生真正理解知识点，而不仅仅是知道答案

请严格按以下 JSON 数组格式返回，不要输出任何其他内容：
```json
[
  {{
    "content": "题目内容",
    "options": ["选项A内容", "选项B内容", "选项C内容", "选项D内容"],
    "answer": "A",
    "analysis": "正确答案是A，因为...(详细解释)。选项B错误是因为...。选项C错误是因为...。选项D错误是因为...",
    "knowledge_point": "知识点名称",
    "difficulty": {difficulty},
    "question_type": "单选"
  }},
  {{
    "content": "解答题题目内容",
    "options": [],
    "answer": "参考答案",
    "analysis": "解题思路：第一步...第二步...第三步...",
    "knowledge_point": "知识点名称",
    "difficulty": {difficulty},
    "question_type": "解答"
  }}
]
```"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的教育出题系统，只输出JSON格式的题目数据，不输出任何其他内容。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=4096
            )

            content = response.choices[0].message.content
            return self._parse_response(content, subject, difficulty)

        except Exception as e:
            print(f'AI 出题失败: {e}')
            return []

    def _parse_response(self, content, subject, default_difficulty):
        """解析 AI 返回的 JSON 题目数据"""
        # 尝试提取 ```json ... ``` 块
        json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # 尝试直接解析整个内容
            json_str = content.strip()

        try:
            questions = json.loads(json_str)
        except json.JSONDecodeError:
            # 尝试找到第一个 [ 和最后一个 ]
            start = json_str.find('[')
            end = json_str.rfind(']')
            if start != -1 and end != -1:
                try:
                    questions = json.loads(json_str[start:end + 1])
                except json.JSONDecodeError:
                    print(f'JSON 解析失败: {json_str[:200]}')
                    return []
            else:
                print(f'未找到 JSON 数组: {json_str[:200]}')
                return []

        # 校验并补充字段
        result = []
        for q in questions:
            if not q.get('content') or not q.get('answer'):
                continue
            q_type = q.get('question_type', '单选')
            result.append({
                'content': q['content'],
                'options': q.get('options', []),
                'answer': str(q['answer']),
                'analysis': q.get('analysis', ''),
                'knowledge_point': q.get('knowledge_point', '综合'),
                'difficulty': q.get('difficulty', default_difficulty),
                'question_type': q_type,
                'subject': subject
            })

        return result

    def grade_essay(self, question_content, reference_answer, user_answer, image_path=None):
        """AI 判分解答题

        Args:
            question_content: 题目内容
            reference_answer: 参考答案
            user_answer: 用户的回答

        Returns:
            dict: { is_correct: bool, score: int(0-100), feedback: str }
        """
        prompt = f"""你是一位学科阅卷老师。请对学生的解答进行评分。

【题目】{question_content}

【参考答案】{reference_answer}

【学生回答】{user_answer}
{f"（该学生还上传了手写作答图片：{image_path}，请结合文字回答进行评判）" if image_path else ""}

请按以下 JSON 格式返回评分结果，不要输出其他内容：
```json
{{
  "score": 85,
  "is_correct": true,
  "feedback": "对学生回答的点评，指出优点和不足"
}}
```

评分标准（请宽松评分）：
- 学生的回答只要核心意思正确、包含关键知识点，就应该给高分（80-100）
- 只有核心内容完全错误才给低分（低于60）
- 文字表述不同但意思一致，视为正确
- score >= 60 视为正确（is_correct: true），否则为错误（is_correct: false）
- feedback 要具体、有指导性，用鼓励的语气"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的教育阅卷系统，只输出JSON格式的评分结果。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1024
            )

            content = response.choices[0].message.content
            result = self._parse_report_json(content)

            return {
                'is_correct': result.get('is_correct', False),
                'score': result.get('score', 0),
                'feedback': result.get('feedback', '暂无点评')
            }
        except Exception as e:
            print(f'AI 判分失败: {e}')
            return {
                'is_correct': False,
                'score': 0,
                'feedback': f'AI 判分异常: {str(e)}'
            }

    def _parse_report_json(self, content):
        """解析 AI 返回的学习报告 JSON"""
        json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
        json_str = json_match.group(1) if json_match else content.strip()

        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            start = json_str.find('{')
            end = json_str.rfind('}')
            if start != -1 and end != -1:
                try:
                    return json.loads(json_str[start:end + 1])
                except json.JSONDecodeError:
                    pass
            # 解析失败时返回兜底结构
            return {
                'summary': content[:200],
                'progress': '',
                'weak_analysis': '',
                'suggestions': ['建议多做练习题巩固知识点'],
                'study_plan': '请根据薄弱知识点进行针对性练习'
            }
