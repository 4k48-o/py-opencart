"""
FastAPI dependencies for authentication and authorization
"""
import logging
from typing import Optional, Type, TypeVar, Callable
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.models.system.user import User
from app.models.system.api import Api
from app.core.security import verify_token, verify_password
from app.core.permissions import get_user_permissions, check_permission
import json

logger = logging.getLogger(__name__)

# 服务层依赖注入类型变量
T = TypeVar('T')

# HTTP Bearer Token security
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """
    获取当前用户（JWT Token认证）
    
    Args:
        credentials: HTTP Bearer Token凭证
        
    Returns:
        User: 当前用户模型实例
        
    Raises:
        HTTPException: Token无效或用户不存在
    """
    token = credentials.credentials
    payload = verify_token(token)
    
    # 验证Token类型
    if payload.get("type") != "access":
        logger.warning(f"Token类型错误: type={payload.get('type')}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload missing user ID",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        user = await User.get_or_none(user_id=int(user_id), status=1)
        if not user:
            logger.warning(f"用户不存在或已禁用: user_id={user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or disabled",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    except (ValueError, TypeError) as e:
        logger.error(f"用户ID格式错误: user_id={user_id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID format",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def verify_api_key(
    x_api_key: str = Header(..., alias="X-API-Key", description="API密钥")
) -> Api:
    """
    验证API密钥
    
    Args:
        x_api_key: API密钥（从请求头获取）
        
    Returns:
        Api: API密钥模型实例
        
    Raises:
        HTTPException: API密钥无效或禁用
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required",
        )
    
    # 查询所有启用的API密钥
    # 注意：这里需要遍历所有API密钥进行验证（因为key是加密存储的）
    # 实际应用中应该优化为使用索引或缓存
    api_keys = await Api.filter(status=1).all()
    
    for api in api_keys:
        if not api.key:
            continue
        
        # 尝试使用密码验证（bcrypt）
        try:
            if verify_password(x_api_key, api.key):
                return api
        except Exception:
            # 如果验证失败，可能是旧数据（明文存储），尝试直接比较
            # 注意：生产环境应该移除这个兼容逻辑
            if api.key == x_api_key:
                logger.warning(f"API密钥使用明文存储（应尽快迁移）: api_id={api.api_id}")
                return api
    
    # 没有找到匹配的API密钥
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API key",
    )


def require_permission(permission: str):
    """
    权限验证依赖工厂函数
    
    Args:
        permission: 需要的权限，格式为 "resource:action"
        
    Returns:
        Callable: 权限验证依赖函数
    """
    async def permission_checker(
        current_user: User = Depends(get_current_user)
    ) -> bool:
        """
        权限验证依赖函数
        
        Args:
            current_user: 当前用户（由get_current_user提供）
            
        Returns:
            bool: 验证通过返回True
            
        Raises:
            HTTPException: 权限不足
        """
        has_permission = await check_permission(current_user, permission)
        if not has_permission:
            logger.warning(
                f"权限不足: user_id={current_user.user_id}, "
                f"username={current_user.username}, required={permission}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission}",
            )
        return True
    
    return permission_checker


def require_any_permission(*permissions: str):
    """
    验证是否有任一权限
    
    Args:
        *permissions: 权限列表
        
    Returns:
        Callable: 权限验证依赖函数
    """
    async def permission_checker(
        current_user: User = Depends(get_current_user)
    ) -> bool:
        user_permissions = await get_user_permissions(current_user)
        if not any(perm in user_permissions for perm in permissions):
            logger.warning(
                f"权限不足: user_id={current_user.user_id}, "
                f"username={current_user.username}, required=any of {permissions}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied",
            )
        return True
    
    return permission_checker


def require_all_permissions(*permissions: str):
    """
    验证是否有所有权限
    
    Args:
        *permissions: 权限列表
        
    Returns:
        Callable: 权限验证依赖函数
    """
    async def permission_checker(
        current_user: User = Depends(get_current_user)
    ) -> bool:
        user_permissions = await get_user_permissions(current_user)
        if not all(perm in user_permissions for perm in permissions):
            logger.warning(
                f"权限不足: user_id={current_user.user_id}, "
                f"username={current_user.username}, required=all of {permissions}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied",
            )
        return True
    
    return permission_checker


# ==================== 服务层依赖注入 ====================

def get_service(service_class: Type[T]) -> Callable[[], T]:
    """
    服务层依赖注入工厂函数
    
    用于在路由中注入服务层实例
    
    Args:
        service_class: 服务类（继承自BaseService）
        
    Returns:
        Callable: 返回服务实例的依赖函数
        
    Example:
        ```python
        @router.get("/")
        async def list_items(
            service: AttributeGroupService = Depends(get_service(AttributeGroupService))
        ):
            return await service.list_attribute_groups(...)
        ```
    """
    def _get_service() -> T:
        """返回服务实例"""
        return service_class()
    
    return _get_service

