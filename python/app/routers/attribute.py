"""
Attribute API router
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

from app.schemas.attribute import (
    AttributeCreate, AttributeUpdate, AttributeResponse
)
from app.services.attribute_service import AttributeService
from app.exceptions import NotFoundException, ConflictException, ValidationException
from app.api.deps import get_current_user, require_permission, get_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/attributes", tags=["attributes"])


@router.get("/", response_model=List[AttributeResponse], summary="获取属性列表")
async def list_attributes(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(20, ge=1, le=100, description="返回的记录数"),
    sort: str = Query("sort_order", description="排序字段"),
    order: str = Query("asc", description="排序方向"),
    filter_name: Optional[str] = Query(None, alias="filter[name]", description="按名称筛选"),
    filter_attribute_group_id: Optional[int] = Query(None, alias="filter[attribute_group_id]", ge=1, description="按属性组ID筛选"),
    language_id: Optional[int] = Query(None, ge=1, description="语言ID"),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("attribute:read")),
    service: AttributeService = Depends(get_service(AttributeService)),
):
    """
    获取属性列表
    
    - **skip**: 跳过的记录数
    - **limit**: 返回的记录数（最大100）
    - **sort**: 排序字段（sort_order, attribute_group_id）
    - **order**: 排序方向（asc, desc）
    - **filter[name]**: 按名称筛选（模糊匹配）
    - **filter[attribute_group_id]**: 按属性组ID筛选
    - **language_id**: 语言ID
    """
    logger.info(f"开始获取属性列表: skip={skip}, limit={limit}, user_id={current_user.user_id}")
    try:
        return await service.list_attributes(
            skip=skip,
            limit=limit,
            sort=sort,
            order=order,
            filter_name=filter_name,
            filter_attribute_group_id=filter_attribute_group_id,
            language_id=language_id
        )
    except Exception as e:
        logger.error(f"获取属性列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取属性列表失败: {str(e)}"
        )


@router.get("/{id}", response_model=AttributeResponse, summary="获取属性详情")
async def get_attribute(
    id: int,
    language_id: Optional[int] = Query(None, ge=1, description="语言ID"),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("attribute:read")),
    service: AttributeService = Depends(get_service(AttributeService)),
):
    """
    获取属性详情
    
    - **id**: 属性ID
    - **language_id**: 语言ID
    """
    logger.info(f"开始获取属性详情: id={id}, user_id={current_user.user_id}")
    try:
        return await service.get_attribute(
            attribute_id=id,
            language_id=language_id
        )
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"属性ID {id} 不存在"
        )
    except Exception as e:
        logger.error(f"获取属性详情失败: id={id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取属性详情失败: {str(e)}"
        )


@router.post("/", response_model=AttributeResponse, status_code=status.HTTP_201_CREATED, summary="创建属性")
async def create_attribute(
    attribute_data: AttributeCreate,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("attribute:create")),
    service: AttributeService = Depends(get_service(AttributeService)),
):
    """
    创建新的属性
    
    - **attribute_group_id**: 属性组ID（必填）
    - **sort_order**: 排序
    - **descriptions**: 多语言描述数组（必填）
    """
    logger.info(f"开始创建属性: user_id={current_user.user_id}")
    try:
        return await service.create_attribute(attribute_data)
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.detail.get("message", "验证失败"))
        )
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.detail.get("message", "属性组不存在"))
        )
    except ConflictException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.detail.get("message", "创建失败"))
        )
    except Exception as e:
        logger.error(f"创建属性失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建属性失败: {str(e)}"
        )


@router.put("/{id}", response_model=AttributeResponse, summary="更新属性")
async def update_attribute(
    id: int,
    attribute_data: AttributeCreate,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("attribute:update")),
    service: AttributeService = Depends(get_service(AttributeService)),
):
    """
    完整更新属性
    
    - **id**: 属性ID
    - **attribute_group_id**: 属性组ID
    - **sort_order**: 排序
    - **descriptions**: 多语言描述数组
    """
    logger.info(f"开始更新属性: id={id}, user_id={current_user.user_id}")
    try:
        return await service.update_attribute(
            attribute_id=id,
            data=attribute_data
        )
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"属性ID {id} 不存在"
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.detail.get("message", "验证失败"))
        )
    except Exception as e:
        logger.error(f"更新属性失败: id={id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新属性失败: {str(e)}"
        )


@router.patch("/{id}", response_model=AttributeResponse, summary="部分更新属性")
async def patch_attribute(
    id: int,
    attribute_data: AttributeUpdate,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("attribute:update")),
    service: AttributeService = Depends(get_service(AttributeService)),
):
    """
    部分更新属性
    
    - **id**: 属性ID
    - **attribute_group_id**: 属性组ID（可选）
    - **sort_order**: 排序（可选）
    - **descriptions**: 多语言描述数组（可选）
    """
    logger.info(f"开始部分更新属性: id={id}, user_id={current_user.user_id}")
    try:
        return await service.patch_attribute(
            attribute_id=id,
            data=attribute_data
        )
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"属性ID {id} 不存在"
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.detail.get("message", "验证失败"))
        )
    except Exception as e:
        logger.error(f"部分更新属性失败: id={id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"部分更新属性失败: {str(e)}"
        )


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除属性")
async def delete_attribute(
    id: int,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("attribute:delete")),
    service: AttributeService = Depends(get_service(AttributeService)),
):
    """
    删除属性
    
    - **id**: 属性ID
    
    业务规则：如果属性被商品使用，不允许删除
    """
    logger.info(f"开始删除属性: id={id}, user_id={current_user.user_id}")
    try:
        await service.delete_attribute(attribute_id=id)
        return None
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"属性ID {id} 不存在"
        )
    except ConflictException as e:
        detail_msg = str(e.detail.get("message", "属性已被商品使用，无法删除"))
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
        logger.error(f"删除属性失败: id={id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除属性失败: {str(e)}"
        )


@router.get("/attribute-groups/{group_id}/attributes", response_model=List[AttributeResponse], summary="获取属性组下的属性")
async def get_attribute_group_attributes(
    group_id: int,
    language_id: Optional[int] = Query(None, ge=1, description="语言ID"),
    sort: str = Query("sort_order", description="排序字段"),
    order: str = Query("asc", description="排序方向"),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("attribute:read")),
    service: AttributeService = Depends(get_service(AttributeService)),
):
    """
    获取属性组下的所有属性
    
    - **group_id**: 属性组ID
    - **language_id**: 语言ID
    - **sort**: 排序字段
    - **order**: 排序方向
    """
    logger.info(f"开始获取属性组下的属性: group_id={group_id}, user_id={current_user.user_id}")
    try:
        return await service.get_attribute_group_attributes(
            group_id=group_id,
            language_id=language_id,
            sort=sort,
            order=order
        )
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"属性组ID {group_id} 不存在"
        )
    except Exception as e:
        logger.error(f"获取属性组下的属性失败: group_id={group_id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取属性组下的属性失败: {str(e)}"
        )
