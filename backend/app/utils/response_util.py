"""
统一响应工具模块
所有接口统一使用 success() / fail() 返回标准 JSON 格式
格式: { code: int, message: str, data: any }
"""

from flask import jsonify


def success(data=None, message='操作成功', code=200):
    """统一成功响应

    Args:
        data: 返回数据，默认 None
        message: 提示信息，默认 '操作成功'
        code: HTTP 状态码，默认 200

    Returns:
        Flask Response 对象
    """
    response = jsonify({
        'code': code,
        'message': message,
        'data': data
    })
    if code != 200:
        response.status_code = code
    return response


def fail(message='操作失败', code=400, data=None):
    """统一失败响应

    Args:
        message: 错误提示信息
        code: HTTP 状态码，默认 400
        data: 附加数据，默认 None

    Returns:
        Flask Response 对象
    """
    response = jsonify({
        'code': code,
        'message': message,
        'data': data
    })
    response.status_code = code
    return response
