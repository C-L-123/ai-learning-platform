"""
日志工具模块
提供结构化日志：OCR 识别、AI 大模型调用、用户登录行为
所有关键操作统一记录，便于排查和监控
"""

import logging
import os
from datetime import datetime

# 根 logger
_root_logger = logging.getLogger('ai_learning')


def setup_logging(log_dir='logs', level=logging.INFO):
    """初始化日志系统

    配置控制台 + 文件双输出
    文件按天轮转，保留 30 天
    """
    os.makedirs(log_dir, exist_ok=True)

    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)-8s %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )

    # 控制台
    console = logging.StreamHandler()
    console.setFormatter(formatter)

    # 文件（按天轮转）
    from logging.handlers import TimedRotatingFileHandler
    file_handler = TimedRotatingFileHandler(
        os.path.join(log_dir, 'app.log'),
        when='midnight',
        interval=1,
        backupCount=30,
        encoding='utf-8',
    )
    file_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(console)
    root.addHandler(file_handler)

    _root_logger.info('日志系统初始化完成，输出目录: %s', log_dir)


# ==================== 业务日志 ====================

def log_ocr_action(action, detail, success=True, error=None,
                   user_info=None, extra=None):
    """记录 OCR 识别日志

    Args:
        action: 操作类型 (init/start/success/error)
        detail: 详情（图片路径/模型名称）
        success: 是否成功
        error: 错误信息（失败时）
        user_info: 用户标识
        extra: 附加数据（耗时、文本长度等）
    """
    logger = logging.getLogger('ai_learning.ocr')
    msg = f'[OCR] {action} | {detail}'
    if user_info:
        msg += f' | user={user_info}'
    if extra:
        msg += f' | {extra}'
    if not success and error:
        msg += f' | ERROR: {error}'

    if success:
        logger.info(msg)
    else:
        logger.error(msg)


def log_ai_action(action, detail, success=True, error=None, extra=None):
    """记录 AI 大模型调用日志

    Args:
        action: 操作类型 (init/generate_questions/grade_essay/generate_report)
        detail: 详情（科目/模型名/题目摘要）
        success: 是否成功
        error: 错误信息
        extra: 附加数据（耗时、题目数量等）
    """
    logger = logging.getLogger('ai_learning.llm')
    msg = f'[AI] {action} | {detail}'
    if extra:
        msg += f' | {extra}'
    if not success and error:
        msg += f' | ERROR: {error}'

    if success:
        logger.info(msg)
    else:
        logger.error(msg)


def log_login_action(username, result, ip=None, user_id=None, error=None):
    """记录用户登录行为日志

    Args:
        username: 用户名
        result: 登录结果 (success/fail/register)
        ip: 客户端 IP
        user_id: 用户 ID（成功时）
        error: 错误原因（失败时）
    """
    logger = logging.getLogger('ai_learning.auth')
    msg = f'[AUTH] login | user={username} | result={result}'
    if ip:
        msg += f' | ip={ip}'
    if user_id:
        msg += f' | uid={user_id}'
    if error:
        msg += f' | reason={error}'

    if result == 'success':
        logger.info(msg)
    else:
        logger.warning(msg)
