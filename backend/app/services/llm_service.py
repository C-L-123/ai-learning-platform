"""
LLM 业务服务层
封装所有大模型调用：AI 出题、AI 判分、AI 学情报告生成
单例模式，全局仅初始化一次大模型客户端
所有调用均有日志记录
"""

import time
import logging

from app.utils.logger_util import log_ai_action

logger = logging.getLogger(__name__)


class LLMService:
    """LLM 业务服务"""

    _ai_instance = None

    @classmethod
    def _get_ai_engine(cls):
        """全局单例获取 AI 出题服务实例"""
        if cls._ai_instance is None:
            try:
                from app.utils.ai_question_service import AIQuestionService
                cls._ai_instance = AIQuestionService()
                logger.info('[LLM] AI 出题服务初始化成功（全局单例）')
                log_ai_action('init', 'DeepSeek', True)
            except Exception as e:
                log_ai_action('init', 'DeepSeek', False, error=str(e))
                raise
        return cls._ai_instance

    @classmethod
    def generate_questions(cls, subject='数学', knowledge_point=None,
                           difficulty=1, count=5, question_type=None):
        """AI 生成题目

        Args:
            subject: 科目名称
            knowledge_point: 知识点（可选）
            difficulty: 难度 1-简单 2-中等 3-困难
            count: 生成数量
            question_type: 题型筛选（'单选'/'解答'/None混合）

        Returns:
            list[dict]: 题目列表，失败返回空列表
        """
        log_ai_action('generate_questions', subject,
                      extra={'count': count, 'difficulty': difficulty,
                             'knowledge_point': knowledge_point})
        start_time = time.time()

        try:
            ai = cls._get_ai_engine()
            questions = ai.generate_questions(
                subject=subject,
                knowledge_point=knowledge_point,
                difficulty=difficulty,
                count=count,
                question_type=question_type,
            )
            elapsed = round(time.time() - start_time, 2)
            log_ai_action('generate_questions', subject, True,
                          extra={'count': len(questions), 'elapsed': elapsed})
            return questions

        except Exception as e:
            elapsed = round(time.time() - start_time, 2)
            log_ai_action('generate_questions', subject, False,
                          extra={'elapsed': elapsed}, error=str(e))
            return []

    @classmethod
    def grade_essay(cls, question_content, reference_answer, user_answer,
                    image_path=None):
        """AI 判分解答题

        Args:
            question_content: 题目内容
            reference_answer: 参考答案
            user_answer: 用户作答
            image_path: 手写作答图片路径（可选）

        Returns:
            dict: {is_correct, score, feedback}
        """
        log_ai_action('grade_essay', question_content[:50],
                      extra={'has_image': image_path is not None})
        start_time = time.time()

        try:
            ai = cls._get_ai_engine()
            result = ai.grade_essay(
                question_content, reference_answer, user_answer, image_path
            )
            elapsed = round(time.time() - start_time, 2)
            log_ai_action('grade_essay', question_content[:50], True,
                          extra={'score': result.get('score'), 'elapsed': elapsed})
            return result

        except Exception as e:
            elapsed = round(time.time() - start_time, 2)
            log_ai_action('grade_essay', question_content[:50], False,
                          extra={'elapsed': elapsed}, error=str(e))
            return {
                'is_correct': False,
                'score': 0,
                'feedback': f'AI 判分异常: {str(e)}',
            }

    @classmethod
    def generate_study_report(cls, data_context, prompt):
        """AI 生成个性化学习报告

        Args:
            data_context: 学生学习数据文本
            prompt: 完整的提示词

        Returns:
            dict: 报告内容

        Raises:
            Exception: AI 调用失败时抛出
        """
        log_ai_action('generate_report', 'study_report')
        start_time = time.time()

        try:
            ai = cls._get_ai_engine()
            response = ai.client.chat.completions.create(
                model=ai.model,
                messages=[
                    {"role": "system",
                     "content": "你是一位专业的教育学习分析师，只输出JSON格式的报告，不输出任何其他内容。"},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=2048,
            )

            content = response.choices[0].message.content
            report = ai._parse_report_json(content)

            elapsed = round(time.time() - start_time, 2)
            log_ai_action('generate_report', 'study_report', True,
                          extra={'elapsed': elapsed})
            return report

        except Exception as e:
            elapsed = round(time.time() - start_time, 2)
            log_ai_action('generate_report', 'study_report', False,
                          extra={'elapsed': elapsed}, error=str(e))
            raise
