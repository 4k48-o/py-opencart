"""
Option API router
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

from app.schemas.option import OptionCreate, OptionUpdate, OptionResponse
from app.services.option_service import OptionService
from app.exceptions import NotFoundException, ConflictException, ValidationException
from app.api.deps import get_current_user, require_permission, get_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/options", tags=["options"])


@router.get("/", response_model=List[OptionResponse], summary="获取选项列表")
async def list_options(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(20, ge=1, le=100, description="返回的记录数"),
    sort: str = Query("sort_order", description="排序字段"),
    order: str = Query("asc", description="排序方向"),
    filter_name: Optional[str] = Query(None, alias="filter[name]", description="按名称筛选"),
    filter_type: Optional[str] = Query(None, alias="filter[type]", description="按选项类型筛选"),
    language_id: Optional[int] = Query(None, ge=1, description="语言ID"),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("option:read")),
    service: OptionService = Depends(get_service(OptionService)),
):
    """
    获取选项列表
    
    - **skip**: 跳过的记录数
    - **limit**: 返回的记录数（最大100）
    - **sort**: 排序字段（sort_order）
    - **order**: 排序方向（asc, desc）
    - **filter[name]**: 按名称筛选（模糊匹配）
    - **filter[type]**: 按选项类型筛选
    - **language_id**: 语言ID
    """
    logger.info(f"开始获取选项列表: skip={skip}, limit={limit}, user_id={current_user.user_id}")
    try:
        return await service.list_options(
            skip=skip,
            limit=limit,
            sort=sort,
            order=order,
            filter_name=filter_name,
            filter_type=filter_type,
            language_id=language_id
        )
    except Exception as e:
        logger.error(f"获取选项列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取选项列表失败: {str(e)}"
        )


@router.get("/{id}", response_model=OptionResponse, summary="获取选项详情")
async def get_option(
    id: int,
    language_id: Optional[int] = Query(None, ge=1, description="语言ID"),
    include_values: bool = Query(False, description="是否包含选项值列表"),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("option:read")),
    service: OptionService = Depends(get_service(OptionService)),
):
    """
    获取选项详情
    
    - **id**: 选项ID
    - **language_id**: 语言ID
    - **include_values**: 是否包含选项值列表
    """
    logger.info(f"开始获取选项详情: id={id}, user_id={current_user.user_id}")
    try:
        return await service.get_option(
            option_id=id,
            language_id=language_id,
            include_values=include_values
        )
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"选项ID {id} 不存在"
        )
    except Exception as e:
        logger.error(f"获取选项详情失败: id={id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取选项详情失败: {str(e)}"
        )


@router.post("/", response_model=OptionResponse, status_code=status.HTTP_201_CREATED, summary="创建选项")
async def create_option(
    option_data: OptionCreate,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("option:create")),
    service: OptionService = Depends(get_service(OptionService)),
):
    """
    创建新的选项
    
    - **type**: 选项类型（必填）
    - **validation**: 验证规则（可选）
    - **sort_order**: 排序
    - **descriptions**: 多语言描述数组（必填）
    """
    logger.info(f"开始创建选项: user_id={current_user.user_id}")
    try:
        return await service.create_option(option_data)
    except ValidationException as e:
        detail_msg = e.detail.get("message", "验证失败") if isinstance(e.detail, dict) else str(e.detail)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail_msg
        )
    except ConflictException as e:
        detail_msg = e.detail.get("message", "创建失败") if isinstance(e.detail, dict) else str(e.detail)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail_msg
        )
    except Exception as e:
        logger.error(f"创建选项失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建选项失败: {str(e)}"
        )


@router.put("/{id}", response_model=OptionResponse, summary="更新选项")
async def update_option(
    id: int,
    option_data: OptionCreate,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("option:update")),
    service: OptionService = Depends(get_service(OptionService)),
):
    """
    完整更新选项
    
    - **id**: 选项ID
    - **type**: 选项类型
    - **validation**: 验证规则
    - **sort_order**: 排序
    - **descriptions**: 多语言描述数组
    """
    logger.info(f"开始更新选项: id={id}, user_id={current_user.user_id}")
    try:
        return await service.update_option(option_id=id, data=option_data)
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"选项ID {id} 不存在"
        )
    except ValidationException as e:
        detail_msg = e.detail.get("message", "验证失败") if isinstance(e.detail, dict) else str(e.detail)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail_msg
        )
    except Exception as e:
        logger.error(f"更新选项失败: id={id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新选项失败: {str(e)}"
        )


@router.patch("/{id}", response_model=OptionResponse, summary="部分更新选项")
async def patch_option(
    id: int,
    option_data: OptionUpdate,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("option:update")),
    service: OptionService = Depends(get_service(OptionService)),
):
    """
    部分更新选项
    
    - **id**: 选项ID
    - **type**: 选项类型（可选）
    - **validation**: 验证规则（可选）
    - **sort_order**: 排序（可选）
    - **descriptions**: 多语言描述数组（可选）
    """
    logger.info(f"开始部分更新选项: id={id}, user_id={current_user.user_id}")
    try:
        return await service.patch_option(option_id=id, data=option_data)
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"选项ID {id} 不存在"
        )
    except ValidationException as e:
        detail_msg = e.detail.get("message", "验证失败") if isinstance(e.detail, dict) else str(e.detail)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail_msg
        )
    except Exception as e:
        logger.error(f"部分更新选项失败: id={id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"部分更新选项失败: {str(e)}"
        )


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除选项")
async def delete_option(
    id: int,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("option:delete")),
    service: OptionService = Depends(get_service(OptionService)),
):
    """
    删除选项
    
    - **id**: 选项ID
    
    业务规则：如果选项被商品使用，不允许删除
    """
    logger.info(f"开始删除选项: id={id}, user_id={current_user.user_id}")
    try:
        await service.delete_option(option_id=id)
        return None
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"选项ID {id} 不存在"
        )
    except ConflictException as e:
        detail_msg = e.detail.get("message", "选项已被商品使用，无法删除") if isinstance(e.detail, dict) else str(e.detail)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail_msg
        )
    except Exception as e:
        logger.error(f"删除选项失败: id={id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除选项失败: {str(e)}"
        )

