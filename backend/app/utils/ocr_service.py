import json
import re
from paddleocr import PaddleOCR


# 默认的知识点关键词映射（数据库无数据时的兜底）
DEFAULT_KNOWLEDGE_MAPPING = {
    '数学': [
        '函数', '导数', '积分', '极限', '数列', '三角函数', '向量',
        '立体几何', '解析几何', '概率', '统计', '不等式', '方程',
        '集合', '逻辑', '复数', '矩阵', '排列组合', '二项式定理'
    ],
    '英语': [
        '语法', '词汇', '阅读理解', '完形填空', '写作', '听力',
        '时态', '语态', '从句', '非谓语动词', '介词', '冠词'
    ],
    '物理': [
        '力学', '电磁学', '光学', '热学', '原子物理', '运动学',
        '牛顿定律', '能量守恒', '动量守恒', '电场', '磁场', '电路'
    ],
    '化学': [
        '有机化学', '无机化学', '化学反应', '化学平衡', '电化学',
        '元素周期', '化学键', '溶液', '氧化还原', '物质结构'
    ]
}


class OCRService:
    def __init__(self):
        self.ocr = PaddleOCR(use_doc_orientation_classify=True, lang='ch')

    def recognize_image(self, image_path):
        """识别图片内容"""
        result = self.ocr.ocr(image_path, cls=True)
        text_lines = []

        if result and result[0]:
            for line in result[0]:
                text_lines.append(line[1][0])

        return '\n'.join(text_lines)

    def extract_knowledge_points(self, text, subject='数学', keywords=None):
        """从文本中提取知识点

        Args:
            text: OCR识别的文本
            subject: 科目名称
            keywords: 知识点关键词列表（从数据库读取），为 None 时使用默认映射
        """
        if keywords:
            kw_list = keywords
        else:
            kw_list = DEFAULT_KNOWLEDGE_MAPPING.get(subject, DEFAULT_KNOWLEDGE_MAPPING['数学'])

        found_points = []
        for keyword in kw_list:
            if keyword in text:
                found_points.append(keyword)

        # 如果没有找到，返回默认知识点
        if not found_points:
            found_points = ['综合应用']

        return list(set(found_points))

    def analyze_mastery(self, knowledge_points, text):
        """分析掌握度（模拟）"""
        mastery = {}
        for point in knowledge_points:
            count = text.count(point)
            base_rate = 60 + count * 10
            mastery[point] = min(base_rate, 95)

        return mastery

    def generate_analysis_report(self, text, subject='数学', keywords=None):
        """生成完整的学情分析报告

        Args:
            text: OCR识别的文本
            subject: 科目名称
            keywords: 知识点关键词列表（从数据库读取）
        """
        knowledge_points = self.extract_knowledge_points(text, subject, keywords)
        mastery = self.analyze_mastery(knowledge_points, text)

        weak_points = [k for k, v in mastery.items() if v < 70]

        report = {
            'total_content_length': len(text),
            'knowledge_points': knowledge_points,
            'mastery_level': mastery,
            'weak_points': weak_points,
            'suggestions': self.generate_suggestions(weak_points)
        }

        return report

    def generate_suggestions(self, weak_points):
        """生成学习建议"""
        if not weak_points:
            return ['知识点掌握良好，建议继续保持，进行综合练习提升']

        suggestions = []
        for point in weak_points:
            suggestions.append(f'针对【{point}】知识点，建议加强基础概念学习，多做相关练习题')

        suggestions.append('建议使用智能刷题功能，针对薄弱知识点进行专项训练')
        return suggestions
