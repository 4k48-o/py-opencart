"""
业务异常类
"""
from fastapi import HTTPException, status
from typing import Optional, Dict, Any


class BusinessException(HTTPException):
    """业务异常基类"""
    
    def __init__(
        self,
        message: str,
        code: str = "BUSINESS_ERROR",
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        初始化业务异常
        
        Args:
            message: 错误消息
            code: 错误代码
            status_code: HTTP状态码
            details: 详细信息（可选）
        """
        detail = {
            "code": code,
            "message": message
        }
        if details:
            detail["details"] = details
        
        super().__init__(status_code=status_code, detail=detail)
        self.code = code
        self.details = details


class NotFoundException(BusinessException):
    """资源不存在异常"""
    
    def __init__(self, resource: str, resource_id: int):
        """
        初始化资源不存在异常
        
        Args:
            resource: 资源名称（如 "属性组", "属性"）
            resource_id: 资源ID
        """
        super().__init__(
            message=f"{resource} ID {resource_id} 不存在",
            code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"resource": resource, "resource_id": resource_id}
        )


class ConflictException(BusinessException):
    """资源冲突异常"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        初始化资源冲突异常
        
        Args:
            message: 错误消息
            details: 详细信息（可选）
        """
        super().__init__(
            message=message,
            code="CONFLICT",
            status_code=status.HTTP_409_CONFLICT,
            details=details
        )


class ValidationException(BusinessException):
    """验证异常"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        初始化验证异常
        
        Args:
            message: 错误消息
            details: 详细信息（可选）
        """
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )


class UnauthorizedException(BusinessException):
    """未授权异常"""
    
    def __init__(self, message: str = "未授权访问"):
        """
        初始化未授权异常
        
        Args:
            message: 错误消息
        """
        super().__init__(
            message=message,
            code="UNAUTHORIZED",
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class ForbiddenException(BusinessException):
    """禁止访问异常"""
    
    def __init__(self, message: str = "禁止访问"):
        """
        初始化禁止访问异常
        
        Args:
            message: 错误消息
        """
        super().__init__(
            message=message,
            code="FORBIDDEN",
            status_code=status.HTTP_403_FORBIDDEN
        )

