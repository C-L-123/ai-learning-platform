"""
文件校验工具模块
对上传文件进行后缀名和大小校验
主要用于 OCR 上传接口和刷题图片上传接口
"""

import os
from config import Config


def allowed_image_file(filename):
    """校验文件后缀是否为允许的图片格式

    Args:
        filename: 文件名

    Returns:
        bool: 后缀合法返回 True，否则返回 False
    """
    if not filename or '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in Config.ALLOWED_IMAGE_EXTENSIONS


def get_file_extension(filename):
    """获取文件后缀名（小写）

    Args:
        filename: 文件名

    Returns:
        str: 后缀名，无后缀返回空字符串
    """
    if not filename or '.' not in filename:
        return ''
    return filename.rsplit('.', 1)[1].lower()


def validate_image_file(file_obj):
    """校验上传的图片文件（后缀 + 大小）

    校验顺序：
    1. 文件对象是否为空
    2. 文件名是否为空
    3. 文件后缀是否合法
    4. 文件大小是否超限

    Args:
        file_obj: Flask request.files 中的文件对象

    Returns:
        tuple: (is_valid: bool, error_message: str|None)
            - is_valid=True 时 error_message 为 None
            - is_valid=False 时 error_message 为具体错误原因
    """
    # 1. 检查文件对象
    if file_obj is None:
        return False, '没有上传文件'

    # 2. 检查文件名
    if not file_obj.filename or file_obj.filename == '':
        return False, '没有选择文件'

    # 3. 检查文件后缀
    if not allowed_image_file(file_obj.filename):
        allowed = '、'.join(sorted(Config.ALLOWED_IMAGE_EXTENSIONS))
        return False, f'不支持的文件格式，仅支持：{allowed}'

    # 4. 检查文件大小
    file_obj.seek(0, os.SEEK_END)
    file_size = file_obj.tell()
    file_obj.seek(0)

    if file_size > Config.MAX_CONTENT_LENGTH:
        max_mb = Config.MAX_CONTENT_LENGTH // (1024 * 1024)
        return False, f'文件大小超过限制（最大 {max_mb}MB）'

    return True, None
