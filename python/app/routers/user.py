"""
User management API router
"""
import logging
from fastapi import APIRouter, HTTPException, Query, status, Depends
from typing import List, Optional

from app.models.system.user import User
from app.schemas.user import (
    UserCreate, UserUpdate, UserResponse,
    UserGroupCreate, UserGroupUpdate, UserGroupResponse,
    PermissionUpdate, PermissionListResponse, UserActivityResponse,
)
from app.services.user_service import UserService
from app.exceptions import NotFoundException, ConflictException, ValidationException
from app.api.deps import get_current_user, require_permission, get_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/users", tags=["users"])


# ==================== User CRUD ====================

@router.get("/", response_model=List[UserResponse], summary="获取用户列表")
async def list_users(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的记录数"),
    status: Optional[int] = Query(None, ge=0, le=1, description="状态筛选 (0=禁用, 1=启用)"),
    user_group_id: Optional[int] = Query(None, ge=0, description="用户组ID筛选"),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("user:read")),
    service: UserService = Depends(get_service(UserService)),
):
    """
    获取用户列表
    
    - **skip**: 跳过的记录数（用于分页）
    - **limit**: 返回的记录数（最大1000）
    - **status**: 状态筛选（可选）
    - **user_group_id**: 用户组ID筛选（可选）
    """
    logger.info(f"开始获取用户列表: skip={skip}, limit={limit}, user_id={current_user.user_id}")
    try:
        return await service.list_users(
            skip=skip,
            limit=limit,
            status=status,
            user_group_id=user_group_id
        )
    except Exception as e:
        logger.error(f"获取用户列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户列表失败: {str(e)}"
        )


@router.get("/{user_id}", response_model=UserResponse, summary="根据ID获取用户")
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("user:read")),
    service: UserService = Depends(get_service(UserService)),
):
    """
    根据ID获取用户信息
    
    - **user_id**: 用户ID
    """
    logger.info(f"开始获取用户信息: user_id={user_id}, user_id={current_user.user_id}")
    try:
        return await service.get_user(user_id=user_id)
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"用户ID {user_id} 不存在"
        )
    except Exception as e:
        logger.error(f"获取用户信息失败: user_id={user_id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户信息失败: {str(e)}"
        )


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="创建新用户")
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("user:create")),
    service: UserService = Depends(get_service(UserService)),
):
    """
    创建新用户
    
    - **username**: 用户名（必填）
    - **password**: 密码（必填，最少6位）
    - **user_group_id**: 用户组ID（必填）
    - **email**: 邮箱（必填）
    - **firstname**: 名字（必填）
    - **lastname**: 姓氏（必填）
    - **status**: 状态（可选，默认1=启用）
    """
    logger.info(f"开始创建用户: username={user_data.username}, user_id={current_user.user_id}")
    try:
        return await service.create_user(user_data)
    except ConflictException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.detail.get("message", "用户名或邮箱已存在"))
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.detail.get("message", "验证失败"))
        )
    except Exception as e:
        logger.error(f"创建用户失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建用户失败: {str(e)}"
        )


@router.put("/{user_id}", response_model=UserResponse, summary="更新用户信息")
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("user:update")),
    service: UserService = Depends(get_service(UserService)),
):
    """
    更新用户信息
    
    - **user_id**: 用户ID
    - **username**: 用户名（可选）
    - **password**: 密码（可选，最少6位）
    - **user_group_id**: 用户组ID（可选）
    - **email**: 邮箱（可选）
    - **firstname**: 名字（可选）
    - **lastname**: 姓氏（可选）
    - **status**: 状态（可选）
    """
    logger.info(f"开始更新用户: user_id={user_id}, user_id={current_user.user_id}")
    try:
        return await service.update_user(user_id=user_id, data=user_data)
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"用户ID {user_id} 不存在"
        )
    except ConflictException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.detail.get("message", "用户名或邮箱已存在"))
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.detail.get("message", "验证失败"))
        )
    except Exception as e:
        logger.error(f"更新用户失败: user_id={user_id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新用户失败: {str(e)}"
        )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除用户")
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("user:delete")),
    service: UserService = Depends(get_service(UserService)),
):
    """
    删除用户
    
    - **user_id**: 用户ID
    """
    logger.info(f"开始删除用户: user_id={user_id}, user_id={current_user.user_id}")
    try:
        await service.delete_user(user_id=user_id)
        return None
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"用户ID {user_id} 不存在"
        )
    except ConflictException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.detail.get("message", "用户正在被使用，无法删除"))
        )
    except Exception as e:
        logger.error(f"删除用户失败: user_id={user_id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除用户失败: {str(e)}"
        )


# ==================== UserGroup Management ====================

@router.get("/groups/", response_model=List[UserGroupResponse], summary="获取用户组列表")
async def list_user_groups(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的记录数"),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("user:read")),
    service: UserService = Depends(get_service(UserService)),
):
    """
    获取用户组列表
    
    - **skip**: 跳过的记录数（用于分页）
    - **limit**: 返回的记录数（最大1000）
    """
    logger.info(f"开始获取用户组列表: user_id={current_user.user_id}")
    try:
        return await service.list_user_groups(skip=skip, limit=limit)
    except Exception as e:
        logger.error(f"获取用户组列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户组列表失败: {str(e)}"
        )


@router.get("/groups/{user_group_id}", response_model=UserGroupResponse, summary="根据ID获取用户组")
async def get_user_group(
    user_group_id: int,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("user:read")),
    service: UserService = Depends(get_service(UserService)),
):
    """
    根据ID获取用户组信息
    
    - **user_group_id**: 用户组ID
    """
    logger.info(f"开始获取用户组信息: user_group_id={user_group_id}, user_id={current_user.user_id}")
    try:
        return await service.get_user_group(user_group_id=user_group_id)
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"用户组ID {user_group_id} 不存在"
        )
    except Exception as e:
        logger.error(f"获取用户组信息失败: user_group_id={user_group_id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户组信息失败: {str(e)}"
        )


@router.post("/groups/", response_model=UserGroupResponse, status_code=status.HTTP_201_CREATED, summary="创建新用户组")
async def create_user_group(
    group_data: UserGroupCreate,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("user:create")),
    service: UserService = Depends(get_service(UserService)),
):
    """
    创建新用户组
    
    - **name**: 用户组名称（必填）
    - **permission**: 权限配置（可选，JSON格式）
    """
    logger.info(f"开始创建用户组: name={group_data.name}, user_id={current_user.user_id}")
    try:
        return await service.create_user_group(group_data)
    except ConflictException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.detail.get("message", "用户组名称已存在"))
        )
    except Exception as e:
        logger.error(f"创建用户组失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建用户组失败: {str(e)}"
        )


@router.put("/groups/{user_group_id}", response_model=UserGroupResponse, summary="更新用户组信息")
async def update_user_group(
    user_group_id: int,
    group_data: UserGroupUpdate,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("user:update")),
    service: UserService = Depends(get_service(UserService)),
):
    """
    更新用户组信息
    
    - **user_group_id**: 用户组ID
    - **name**: 用户组名称（可选）
    - **permission**: 权限配置（可选，JSON格式）
    """
    logger.info(f"开始更新用户组: user_group_id={user_group_id}, user_id={current_user.user_id}")
    try:
        return await service.update_user_group(user_group_id=user_group_id, data=group_data)
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"用户组ID {user_group_id} 不存在"
        )
    except ConflictException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.detail.get("message", "用户组名称已存在"))
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.detail.get("message", "验证失败"))
        )
    except Exception as e:
        logger.error(f"更新用户组失败: user_group_id={user_group_id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新用户组失败: {str(e)}"
        )


@router.delete("/groups/{user_group_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除用户组")
async def delete_user_group(
    user_group_id: int,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("user:delete")),
    service: UserService = Depends(get_service(UserService)),
):
    """
    删除用户组
    
    - **user_group_id**: 用户组ID
    """
    logger.info(f"开始删除用户组: user_group_id={user_group_id}, user_id={current_user.user_id}")
    try:
        await service.delete_user_group(user_group_id=user_group_id)
        return None
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"用户组ID {user_group_id} 不存在"
        )
    except ConflictException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.detail.get("message", "用户组正在被使用，无法删除"))
        )
    except Exception as e:
        logger.error(f"删除用户组失败: user_group_id={user_group_id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除用户组失败: {str(e)}"
        )


# ==================== User Permission Management ====================

@router.get("/groups/{user_group_id}/permissions", response_model=List[PermissionListResponse], summary="获取用户组权限列表")
async def get_user_group_permissions(
    user_group_id: int,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("user:read")),
    service: UserService = Depends(get_service(UserService)),
):
    """
    获取用户组权限列表
    
    - **user_group_id**: 用户组ID
    """
    logger.info(f"开始获取用户组权限: user_group_id={user_group_id}, user_id={current_user.user_id}")
    try:
        return await service.get_user_group_permissions(user_group_id=user_group_id)
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"用户组ID {user_group_id} 不存在"
        )
    except Exception as e:
        logger.error(f"获取用户组权限失败: user_group_id={user_group_id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户组权限失败: {str(e)}"
        )


@router.put("/groups/{user_group_id}/permissions", response_model=UserGroupResponse, summary="更新用户组权限")
async def update_user_group_permissions(
    user_group_id: int,
    permissions: List[PermissionUpdate],
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("user:update")),
    service: UserService = Depends(get_service(UserService)),
):
    """
    更新用户组权限
    
    - **user_group_id**: 用户组ID
    - **permissions**: 权限列表（资源:操作格式）
    """
    logger.info(f"开始更新用户组权限: user_group_id={user_group_id}, user_id={current_user.user_id}")
    try:
        return await service.update_user_group_permissions(
            user_group_id=user_group_id,
            permissions=permissions
        )
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"用户组ID {user_group_id} 不存在"
        )
    except Exception as e:
        logger.error(f"更新用户组权限失败: user_group_id={user_group_id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新用户组权限失败: {str(e)}"
        )


@router.post("/groups/{user_group_id}/permissions", response_model=UserGroupResponse, summary="添加用户组权限")
async def add_user_group_permission(
    user_group_id: int,
    permission: PermissionUpdate,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("user:update")),
    service: UserService = Depends(get_service(UserService)),
):
    """
    添加用户组权限（合并到现有权限）
    
    - **user_group_id**: 用户组ID
    - **permission**: 要添加的权限
    """
    logger.info(f"开始添加用户组权限: user_group_id={user_group_id}, user_id={current_user.user_id}")
    try:
        return await service.add_user_group_permission(
            user_group_id=user_group_id,
            permission=permission
        )
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"用户组ID {user_group_id} 不存在"
        )
    except Exception as e:
        logger.error(f"添加用户组权限失败: user_group_id={user_group_id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"添加用户组权限失败: {str(e)}"
        )


@router.delete("/groups/{user_group_id}/permissions/{resource}", response_model=UserGroupResponse, summary="删除用户组权限")
async def delete_user_group_permission(
    user_group_id: int,
    resource: str,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("user:update")),
    service: UserService = Depends(get_service(UserService)),
):
    """
    删除用户组权限（删除整个资源权限）
    
    - **user_group_id**: 用户组ID
    - **resource**: 资源名称
    """
    logger.info(f"开始删除用户组权限: user_group_id={user_group_id}, resource={resource}, user_id={current_user.user_id}")
    try:
        return await service.delete_user_group_permission(
            user_group_id=user_group_id,
            resource=resource
        )
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"用户组ID {user_group_id} 不存在"
        )
    except Exception as e:
        logger.error(f"删除用户组权限失败: user_group_id={user_group_id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除用户组权限失败: {str(e)}"
        )


@router.get("/{user_id}/permissions", response_model=List[str], summary="获取用户权限")
async def get_user_permissions(
    user_id: int,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("user:read")),
    service: UserService = Depends(get_service(UserService)),
):
    """
    获取用户权限列表
    
    - **user_id**: 用户ID
    """
    logger.info(f"开始获取用户权限: user_id={user_id}, user_id={current_user.user_id}")
    try:
        return await service.get_user_permissions(user_id=user_id)
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"用户ID {user_id} 不存在"
        )
    except Exception as e:
        logger.error(f"获取用户权限失败: user_id={user_id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户权限失败: {str(e)}"
        )


# ==================== User Activity Log ====================

@router.get("/{user_id}/activities", response_model=List[UserActivityResponse], summary="获取用户活动日志")
async def get_user_activities(
    user_id: int,
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的记录数"),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("user:read")),
    service: UserService = Depends(get_service(UserService)),
):
    """
    获取用户活动日志（登录记录）
    
    - **user_id**: 用户ID
    - **skip**: 跳过的记录数（用于分页）
    - **limit**: 返回的记录数（最大1000）
    """
    logger.info(f"开始获取用户活动日志: user_id={user_id}, user_id={current_user.user_id}")
    try:
        return await service.get_user_activities(
            user_id=user_id,
            skip=skip,
            limit=limit
        )
    except Exception as e:
        logger.error(f"获取用户活动日志失败: user_id={user_id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户活动日志失败: {str(e)}"
        )


@router.get("/activities/", response_model=List[UserActivityResponse], summary="获取所有用户活动日志")
async def list_all_activities(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的记录数"),
    user_id: Optional[int] = Query(None, ge=0, description="用户ID筛选"),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("user:read")),
    service: UserService = Depends(get_service(UserService)),
):
    """
    获取所有用户活动日志（登录记录）
    
    - **skip**: 跳过的记录数（用于分页）
    - **limit**: 返回的记录数（最大1000）
    - **user_id**: 用户ID筛选（可选）
    """
    logger.info(f"开始获取所有用户活动日志: user_id={current_user.user_id}")
    try:
        return await service.get_user_activities(
            user_id=user_id,
            skip=skip,
            limit=limit
        )
    except Exception as e:
        logger.error(f"获取所有用户活动日志失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取所有用户活动日志失败: {str(e)}"
        )
