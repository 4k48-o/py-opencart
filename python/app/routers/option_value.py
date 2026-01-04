"""
OptionValue API router
"""
import logging
from fastapi import APIRouter, HTTPException, Query, status, Depends
from typing import List, Optional, Dict, Any

try:
    from app.models.system.user import User
except (ImportError, AttributeError):
    import importlib
    user_module = importlib.import_module('app.models.system.user')
    User = user_module.User

from app.schemas.option_value import (
    OptionValueCreate, OptionValueUpdate, OptionValueResponse, OptionValueSortUpdate
)
from app.services.option_value_service import OptionValueService
from app.exceptions import NotFoundException, ConflictException, ValidationException
from app.api.deps import get_current_user, require_permission, get_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/option-values", tags=["option-values"])


@router.get("/{id}", response_model=OptionValueResponse, summary="获取选项值详情")
async def get_option_value(
    id: int,
    language_id: Optional[int] = Query(None, ge=1, description="语言ID"),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("option_value:read")),
    service: OptionValueService = Depends(get_service(OptionValueService)),
):
    """
    获取选项值详情
    
    - **id**: 选项值ID
    - **language_id**: 语言ID
    """
    logger.info(f"开始获取选项值详情: id={id}, user_id={current_user.user_id}")
    try:
        return await service.get_option_value(
            option_value_id=id,
            language_id=language_id
        )
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"选项值ID {id} 不存在"
        )
    except Exception as e:
        logger.error(f"获取选项值详情失败: id={id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取选项值详情失败: {str(e)}"
        )


@router.post("/", response_model=OptionValueResponse, status_code=status.HTTP_201_CREATED, summary="创建选项值")
async def create_option_value(
    option_value_data: OptionValueCreate,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("option_value:create")),
    service: OptionValueService = Depends(get_service(OptionValueService)),
):
    """
    创建新的选项值
    
    - **option_id**: 选项ID（必填）
    - **image**: 选项值图片路径（可选）
    - **sort_order**: 排序
    - **descriptions**: 多语言描述数组（必填）
    """
    logger.info(f"开始创建选项值: user_id={current_user.user_id}")
    try:
        return await service.create_option_value(option_value_data)
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"选项ID {option_value_data.option_id} 不存在"
        )
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
        logger.error(f"创建选项值失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建选项值失败: {str(e)}"
        )


@router.put("/{id}", response_model=OptionValueResponse, summary="更新选项值")
async def update_option_value(
    id: int,
    option_value_data: OptionValueCreate,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("option_value:update")),
    service: OptionValueService = Depends(get_service(OptionValueService)),
):
    """
    完整更新选项值
    
    - **id**: 选项值ID
    - **option_id**: 选项ID
    - **image**: 选项值图片路径
    - **sort_order**: 排序
    - **descriptions**: 多语言描述数组
    """
    logger.info(f"开始更新选项值: id={id}, user_id={current_user.user_id}")
    try:
        return await service.update_option_value(option_value_id=id, data=option_value_data)
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"选项值ID {id} 不存在"
        )
    except ValidationException as e:
        detail_msg = e.detail.get("message", "验证失败") if isinstance(e.detail, dict) else str(e.detail)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail_msg
        )
    except Exception as e:
        logger.error(f"更新选项值失败: id={id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新选项值失败: {str(e)}"
        )


@router.patch("/{id}", response_model=OptionValueResponse, summary="部分更新选项值")
async def patch_option_value(
    id: int,
    option_value_data: OptionValueUpdate,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("option_value:update")),
    service: OptionValueService = Depends(get_service(OptionValueService)),
):
    """
    部分更新选项值
    
    - **id**: 选项值ID
    - **option_id**: 选项ID（可选）
    - **image**: 选项值图片路径（可选）
    - **sort_order**: 排序（可选）
    - **descriptions**: 多语言描述数组（可选）
    """
    logger.info(f"开始部分更新选项值: id={id}, user_id={current_user.user_id}")
    try:
        return await service.patch_option_value(option_value_id=id, data=option_value_data)
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"选项值ID {id} 不存在"
        )
    except ValidationException as e:
        detail_msg = e.detail.get("message", "验证失败") if isinstance(e.detail, dict) else str(e.detail)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail_msg
        )
    except Exception as e:
        logger.error(f"部分更新选项值失败: id={id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"部分更新选项值失败: {str(e)}"
        )


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除选项值")
async def delete_option_value(
    id: int,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("option_value:delete")),
    service: OptionValueService = Depends(get_service(OptionValueService)),
):
    """
    删除选项值
    
    - **id**: 选项值ID
    
    业务规则：如果选项值被商品使用，不允许删除
    """
    logger.info(f"开始删除选项值: id={id}, user_id={current_user.user_id}")
    try:
        await service.delete_option_value(option_value_id=id)
        return None
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"选项值ID {id} 不存在"
        )
    except ConflictException as e:
        detail_msg = e.detail.get("message", "选项值已被商品使用，无法删除") if isinstance(e.detail, dict) else str(e.detail)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail_msg
        )
    except Exception as e:
        logger.error(f"删除选项值失败: id={id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除选项值失败: {str(e)}"
        )


# 选项下的选项值管理接口
@router.get("/options/{option_id}/values", response_model=List[OptionValueResponse], summary="获取选项下的选项值列表")
async def get_option_values(
    option_id: int,
    language_id: Optional[int] = Query(None, ge=1, description="语言ID"),
    sort: str = Query("sort_order", description="排序字段"),
    order: str = Query("asc", description="排序方向"),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("option_value:read")),
    service: OptionValueService = Depends(get_service(OptionValueService)),
):
    """
    获取选项下的所有选项值
    
    - **option_id**: 选项ID
    - **language_id**: 语言ID
    - **sort**: 排序字段
    - **order**: 排序方向
    """
    logger.info(f"开始获取选项下的选项值: option_id={option_id}, user_id={current_user.user_id}")
    try:
        return await service.get_option_values(
            option_id=option_id,
            language_id=language_id,
            sort=sort,
            order=order
        )
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"选项ID {option_id} 不存在"
        )
    except Exception as e:
        logger.error(f"获取选项下的选项值失败: option_id={option_id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取选项下的选项值失败: {str(e)}"
        )


@router.post("/options/{option_id}/values", response_model=OptionValueResponse, status_code=status.HTTP_201_CREATED, summary="为选项创建选项值")
async def create_option_value_for_option(
    option_id: int,
    option_value_data: OptionValueCreate,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("option_value:create")),
    service: OptionValueService = Depends(get_service(OptionValueService)),
):
    """
    为选项创建选项值
    
    - **option_id**: 选项ID（路径参数）
    - **image**: 选项值图片路径（可选）
    - **sort_order**: 排序
    - **descriptions**: 多语言描述数组（必填）
    """
    logger.info(f"开始为选项创建选项值: option_id={option_id}, user_id={current_user.user_id}")
    try:
        return await service.create_option_value_for_option(option_id=option_id, data=option_value_data)
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"选项ID {option_id} 不存在"
        )
    except ValidationException as e:
        detail_msg = e.detail.get("message", "验证失败") if isinstance(e.detail, dict) else str(e.detail)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail_msg
        )
    except Exception as e:
        logger.error(f"创建选项值失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建选项值失败: {str(e)}"
        )


@router.patch("/options/{option_id}/values/sort", summary="批量更新选项值排序")
async def update_option_values_sort(
    option_id: int,
    sort_data: OptionValueSortUpdate,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("option_value:update")),
    service: OptionValueService = Depends(get_service(OptionValueService)),
):
    """
    批量更新选项值的排序
    
    - **option_id**: 选项ID
    - **values**: 选项值排序数组
    """
    logger.info(f"开始批量更新选项值排序: option_id={option_id}, user_id={current_user.user_id}")
    try:
        return await service.update_option_values_sort(option_id=option_id, sort_data=sort_data)
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"选项ID {option_id} 不存在"
        )
    except ValidationException as e:
        detail_msg = e.detail.get("message", "验证失败") if isinstance(e.detail, dict) else str(e.detail)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail_msg
        )
    except Exception as e:
        logger.error(f"批量更新选项值排序失败: option_id={option_id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量更新选项值排序失败: {str(e)}"
        )

