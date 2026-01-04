"""
AttributeGroup API router
"""
import logging
from fastapi import APIRouter, HTTPException, Query, status, Depends
from typing import List, Optional

try:
    from app.models.system.user import User
except (ImportError, AttributeError):
    import importlib
    user_module = importlib.import_module('app.models.system.user')
    User = user_module.User

from app.schemas.attribute_group import (
    AttributeGroupCreate, AttributeGroupUpdate, AttributeGroupResponse
)
from app.services.attribute_group_service import AttributeGroupService
from app.exceptions import NotFoundException, ConflictException, ValidationException
from app.api.deps import get_current_user, require_permission, get_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/attribute-groups", tags=["attribute-groups"])


@router.get("/", response_model=List[AttributeGroupResponse], summary="获取属性组列表")
async def list_attribute_groups(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(20, ge=1, le=100, description="返回的记录数"),
    sort: str = Query("sort_order", description="排序字段"),
    order: str = Query("asc", description="排序方向"),
    filter_name: Optional[str] = Query(None, alias="filter[name]", description="按名称筛选"),
    language_id: Optional[int] = Query(None, ge=1, description="语言ID"),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("attribute_group:read")),
    service: AttributeGroupService = Depends(get_service(AttributeGroupService)),
):
    """
    获取属性组列表
    
    - **skip**: 跳过的记录数
    - **limit**: 返回的记录数（最大100）
    - **sort**: 排序字段（sort_order, name）
    - **order**: 排序方向（asc, desc）
    - **filter[name]**: 按名称筛选（模糊匹配）
    - **language_id**: 语言ID（用于返回对应语言的名称）
    """
    logger.info(f"开始获取属性组列表: skip={skip}, limit={limit}, user_id={current_user.user_id}")
    try:
        return await service.list_attribute_groups(
            skip=skip,
            limit=limit,
            sort=sort,
            order=order,
            filter_name=filter_name,
            language_id=language_id
        )
    except Exception as e:
        logger.error(f"获取属性组列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取属性组列表失败: {str(e)}"
        )


@router.get("/{id}", response_model=AttributeGroupResponse, summary="获取属性组详情")
async def get_attribute_group(
    id: int,
    language_id: Optional[int] = Query(None, ge=1, description="语言ID"),
    include_attributes: bool = Query(False, description="是否包含属性列表"),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("attribute_group:read")),
    service: AttributeGroupService = Depends(get_service(AttributeGroupService)),
):
    """
    获取属性组详情
    
    - **id**: 属性组ID
    - **language_id**: 语言ID
    - **include_attributes**: 是否包含属性列表
    """
    logger.info(f"开始获取属性组详情: id={id}, user_id={current_user.user_id}")
    try:
        return await service.get_attribute_group(
            attribute_group_id=id,
            language_id=language_id
        )
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"属性组ID {id} 不存在"
        )
    except Exception as e:
        logger.error(f"获取属性组详情失败: id={id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取属性组详情失败: {str(e)}"
        )


@router.post("/", response_model=AttributeGroupResponse, status_code=status.HTTP_201_CREATED, summary="创建属性组")
async def create_attribute_group(
    group_data: AttributeGroupCreate,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("attribute_group:create")),
    service: AttributeGroupService = Depends(get_service(AttributeGroupService)),
):
    """
    创建新的属性组
    
    - **sort_order**: 排序
    - **descriptions**: 多语言描述数组（必填）
    """
    logger.info(f"开始创建属性组: user_id={current_user.user_id}")
    try:
        return await service.create_attribute_group(group_data)
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.detail.get("message", "验证失败"))
        )
    except ConflictException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.detail.get("message", "创建失败"))
        )
    except Exception as e:
        logger.error(f"创建属性组失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建属性组失败: {str(e)}"
        )


@router.put("/{id}", response_model=AttributeGroupResponse, summary="更新属性组")
async def update_attribute_group(
    id: int,
    group_data: AttributeGroupCreate,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("attribute_group:update")),
    service: AttributeGroupService = Depends(get_service(AttributeGroupService)),
):
    """
    完整更新属性组
    
    - **id**: 属性组ID
    - **sort_order**: 排序
    - **descriptions**: 多语言描述数组
    """
    logger.info(f"开始更新属性组: id={id}, user_id={current_user.user_id}")
    try:
        return await service.update_attribute_group(
            attribute_group_id=id,
            data=group_data
        )
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"属性组ID {id} 不存在"
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.detail.get("message", "验证失败"))
        )
    except Exception as e:
        logger.error(f"更新属性组失败: id={id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新属性组失败: {str(e)}"
        )


@router.patch("/{id}", response_model=AttributeGroupResponse, summary="部分更新属性组")
async def patch_attribute_group(
    id: int,
    group_data: AttributeGroupUpdate,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("attribute_group:update")),
    service: AttributeGroupService = Depends(get_service(AttributeGroupService)),
):
    """
    部分更新属性组
    
    - **id**: 属性组ID
    - **sort_order**: 排序（可选）
    - **descriptions**: 多语言描述数组（可选）
    """
    logger.info(f"开始部分更新属性组: id={id}, user_id={current_user.user_id}")
    try:
        return await service.patch_attribute_group(
            attribute_group_id=id,
            data=group_data
        )
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"属性组ID {id} 不存在"
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.detail.get("message", "验证失败"))
        )
    except Exception as e:
        logger.error(f"部分更新属性组失败: id={id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"部分更新属性组失败: {str(e)}"
        )


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除属性组")
async def delete_attribute_group(
    id: int,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("attribute_group:delete")),
    service: AttributeGroupService = Depends(get_service(AttributeGroupService)),
):
    """
    删除属性组
    
    - **id**: 属性组ID
    
    业务规则：如果属性组下有属性，不允许删除
    """
    logger.info(f"开始删除属性组: id={id}, user_id={current_user.user_id}")
    try:
        await service.delete_attribute_group(attribute_group_id=id)
        return None
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"属性组ID {id} 不存在"
        )
    except ConflictException as e:
        detail_msg = str(e.detail.get("message", "属性组下存在属性，无法删除"))
        details = e.detail.get("details", {})
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "CONFLICT",
                "message": detail_msg,
                "details": details
            }
        )
    except Exception as e:
        logger.error(f"删除属性组失败: id={id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除属性组失败: {str(e)}"
        )
