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

    def generate_questions(self, subject, knowledge_point=None, difficulty=1, count=5):
        """调用 AI 生成指定科目的题目

        Args:
            subject: 科目名称，如 数学、英语、物理
            knowledge_point: 知识点（可选）
            difficulty: 难度 1-简单 2-中等 3-困难
            count: 生成数量

        Returns:
            list[dict] 题目列表，每项包含 content/options/answer/analysis/knowledge_point/difficulty
        """
        difficulty_map = {1: '简单', 2: '中等', 3: '困难'}
        diff_label = difficulty_map.get(difficulty, '中等')

        kp_hint = f'，知识点为「{knowledge_point}」' if knowledge_point else ''

        prompt = f"""你是一位专业的{subject}学科出题老师。请生成 {count} 道{subject}科目的单选题。

要求：
- 难度：{diff_label}{kp_hint}
- 每道题必须有4个选项（A/B/C/D）
- 每道题必须有正确答案和详细解析
- 题目内容要准确、科学，不能有知识性错误

请严格按以下 JSON 数组格式返回，不要输出任何其他内容：
```json
[
  {{
    "content": "题目内容",
    "options": ["选项A内容", "选项B内容", "选项C内容", "选项D内容"],
    "answer": "A",
    "analysis": "解析说明",
    "knowledge_point": "知识点名称",
    "difficulty": {difficulty}
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
            result.append({
                'content': q['content'],
                'options': q.get('options', []),
                'answer': str(q['answer']),
                'analysis': q.get('analysis', ''),
                'knowledge_point': q.get('knowledge_point', '综合'),
                'difficulty': q.get('difficulty', default_difficulty),
                'question_type': '单选',
                'subject': subject
            })

        return result

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
