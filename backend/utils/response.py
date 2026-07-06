"""
统一响应格式工具类
提供标准化的 success/fail 响应方法
"""
from flask import jsonify
from typing import Any, Dict, Optional


class ResponseCode:
    """HTTP 状态码枚举"""
    SUCCESS = 200
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    SERVER_ERROR = 500


def success(data: Any = None, message: str = "success", code: int = ResponseCode.SUCCESS) -> Dict:
    """
    成功响应
    
    Args:
        data: 返回数据
        message: 提示信息
        code: HTTP 状态码，默认 200
    
    Returns:
        标准化响应格式
    """
    return jsonify({
        "code": code,
        "message": message,
        "data": data,
        "status": "success"
    }), code


def fail(message: str = "error", code: int = ResponseCode.BAD_REQUEST, data: Any = None) -> Dict:
    """
    失败响应
    
    Args:
        message: 错误提示信息
        code: HTTP 状态码，默认 400
        data: 附加数据
    
    Returns:
        标准化响应格式
    """
    return jsonify({
        "code": code,
        "message": message,
        "data": data,
        "status": "error"
    }), code


def error_401(message: str = "Unauthorized") -> Dict:
    """401 未授权"""
    return fail(message=message, code=ResponseCode.UNAUTHORIZED)


def error_400(message: str = "Bad Request") -> Dict:
    """400 请求错误"""
    return fail(message=message, code=ResponseCode.BAD_REQUEST)


def error_500(message: str = "Internal Server Error") -> Dict:
    """500 服务器错误"""
    return fail(message=message, code=ResponseCode.SERVER_ERROR)
