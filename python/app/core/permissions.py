"""
Permission utilities for RBAC
"""
import json
import logging
from typing import List, Optional
from app.models.system.user import User
from app.models.system.user_group import UserGroup

logger = logging.getLogger(__name__)


async def get_user_permissions(user: User) -> List[str]:
    """
    获取用户权限列表
    
    Args:
        user: User模型实例
        
    Returns:
        List[str]: 权限列表，格式为 ["resource:action", ...]
    """
    try:
        user_group = await user.get_user_group()
        if not user_group or not user_group.permission:
            return []
        
        permissions_dict = json.loads(user_group.permission)
        permissions = []
        for resource, actions in permissions_dict.items():
            if isinstance(actions, list):
                for action in actions:
                    permissions.append(f"{resource}:{action}")
        
        return permissions
    except (json.JSONDecodeError, TypeError, AttributeError) as e:
        logger.error(f"解析用户权限失败: user_id={user.user_id}, error={str(e)}")
        return []


async def check_permission(user: User, required_permission: str) -> bool:
    """
    检查用户是否有指定权限
    
    Args:
        user: User模型实例
        required_permission: 需要的权限，格式为 "resource:action"
        
    Returns:
        bool: 是否有权限
    """
    user_permissions = await get_user_permissions(user)
    return required_permission in user_permissions


async def check_any_permission(user: User, *permissions: str) -> bool:
    """
    检查用户是否有任一权限
    
    Args:
        user: User模型实例
        *permissions: 权限列表
        
    Returns:
        bool: 是否有任一权限
    """
    user_permissions = await get_user_permissions(user)
    return any(perm in user_permissions for perm in permissions)


async def check_all_permissions(user: User, *permissions: str) -> bool:
    """
    检查用户是否有所有权限
    
    Args:
        user: User模型实例
        *permissions: 权限列表
        
    Returns:
        bool: 是否有所有权限
    """
    user_permissions = await get_user_permissions(user)
    return all(perm in user_permissions for perm in permissions)

