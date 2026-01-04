"""
Store API router
"""
import logging
from fastapi import APIRouter, HTTPException, Query, status, Depends
from typing import List

try:
    from app.models.system.user import User
except (ImportError, AttributeError):
    import importlib
    user_module = importlib.import_module('app.models.system.user')
    User = user_module.User

from app.schemas.store import StoreCreate, StoreUpdate, StoreResponse
from app.services.store_service import StoreService
from app.exceptions import NotFoundException, ConflictException, ValidationException
from app.api.deps import get_current_user, require_permission, get_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/stores", tags=["stores"])


@router.get("/", response_model=List[StoreResponse], summary="获取店铺列表")
async def list_stores(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的记录数"),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("store:read")),
    service: StoreService = Depends(get_service(StoreService)),
):
    """
    获取店铺列表
    
    - **skip**: 跳过的记录数（用于分页）
    - **limit**: 返回的记录数（最大1000）
    """
    logger.info(f"开始获取店铺列表: skip={skip}, limit={limit}, user_id={current_user.user_id}")
    try:
        return await service.list_stores(skip=skip, limit=limit)
    except Exception as e:
        logger.error(f"获取店铺列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取店铺列表失败: {str(e)}"
        )


@router.get("/{store_id}", response_model=StoreResponse, summary="根据ID获取店铺")
async def get_store(
    store_id: int,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("store:read")),
    service: StoreService = Depends(get_service(StoreService)),
):
    """
    根据ID获取店铺信息
    
    - **store_id**: 店铺ID
    """
    logger.info(f"开始获取店铺信息: store_id={store_id}, user_id={current_user.user_id}")
    try:
        return await service.get_store(store_id=store_id)
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"店铺ID {store_id} 不存在"
        )
    except Exception as e:
        logger.error(f"获取店铺信息失败: store_id={store_id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取店铺信息失败: {str(e)}"
        )


@router.post("/", response_model=StoreResponse, status_code=status.HTTP_201_CREATED, summary="创建新店铺")
async def create_store(
    store_data: StoreCreate,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("store:create")),
    service: StoreService = Depends(get_service(StoreService)),
):
    """
    创建新店铺
    
    - **name**: 店铺名称（必填）
    - **url**: 店铺URL（必填）
    """
    logger.info(f"开始创建店铺: name={store_data.name}, user_id={current_user.user_id}")
    try:
        return await service.create_store(store_data)
    except ConflictException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.detail.get("message", "店铺名称已存在"))
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.detail.get("message", "验证失败"))
        )
    except Exception as e:
        logger.error(f"创建店铺失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建店铺失败: {str(e)}"
        )


@router.put("/{store_id}", response_model=StoreResponse, summary="更新店铺信息")
async def update_store(
    store_id: int,
    store_data: StoreUpdate,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("store:update")),
    service: StoreService = Depends(get_service(StoreService)),
):
    """
    更新店铺信息
    
    - **store_id**: 店铺ID
    - **name**: 店铺名称（可选）
    - **url**: 店铺URL（可选）
    """
    logger.info(f"开始更新店铺: store_id={store_id}, user_id={current_user.user_id}")
    try:
        return await service.update_store(store_id=store_id, data=store_data)
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"店铺ID {store_id} 不存在"
        )
    except ConflictException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.detail.get("message", "店铺名称已存在"))
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.detail.get("message", "验证失败"))
        )
    except Exception as e:
        logger.error(f"更新店铺失败: store_id={store_id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新店铺失败: {str(e)}"
        )


@router.delete("/{store_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除店铺")
async def delete_store(
    store_id: int,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("store:delete")),
    service: StoreService = Depends(get_service(StoreService)),
):
    """
    删除店铺
    
    - **store_id**: 店铺ID
    
    注意：删除前会检查是否有其他数据引用该店铺
    """
    logger.info(f"开始删除店铺: store_id={store_id}, user_id={current_user.user_id}")
    try:
        await service.delete_store(store_id=store_id)
        return None
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"店铺ID {store_id} 不存在"
        )
    except ConflictException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.detail.get("message", "店铺正在被使用，无法删除"))
        )
    except Exception as e:
        logger.error(f"删除店铺失败: store_id={store_id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除店铺失败: {str(e)}"
        )
