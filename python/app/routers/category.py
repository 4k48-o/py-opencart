"""
Category API router
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

from app.schemas.category import (
    CategoryCreate, CategoryUpdate, CategoryResponse,
    CategoryTreeItem, CategoryPathResponse, CategoryMoveRequest
)
from app.services.category_service import CategoryService
from app.exceptions import NotFoundException, ConflictException, ValidationException
from app.api.deps import get_current_user, require_permission, get_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/categories", tags=["categories"])


@router.get("/tree", response_model=List[CategoryTreeItem], summary="获取分类树")
async def get_category_tree(
    parent_id: int = Query(0, ge=0, description="父分类ID（默认0，根分类）"),
    language_id: Optional[int] = Query(None, ge=1, description="语言ID"),
    status: Optional[int] = Query(None, ge=0, le=1, description="状态筛选（0=禁用，1=启用）"),
    depth: Optional[int] = Query(None, ge=1, description="最大深度"),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("category:read")),
    service: CategoryService = Depends(get_service(CategoryService)),
):
    """
    获取分类树
    
    - **parent_id**: 父分类ID（默认0，根分类）
    - **language_id**: 语言ID
    - **status**: 状态筛选
    - **depth**: 最大深度
    """
    logger.info(f"开始获取分类树: parent_id={parent_id}, user_id={current_user.user_id}")
    try:
        tree = await service.get_category_tree(parent_id, language_id, status, depth)
        logger.info(f"分类树获取完成: parent_id={parent_id}, count={len(tree)}")
        return tree
    except Exception as e:
        logger.error(f"获取分类树失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取分类树失败: {str(e)}"
        )


@router.get("/", response_model=List[CategoryResponse], summary="获取分类列表")
async def list_categories(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(20, ge=1, le=100, description="返回的记录数"),
    sort: str = Query("sort_order", description="排序字段"),
    order: str = Query("asc", description="排序方向"),
    filter_name: Optional[str] = Query(None, alias="filter[name]", description="按名称筛选"),
    filter_parent_id: Optional[int] = Query(None, alias="filter[parent_id]", ge=0, description="按父分类ID筛选"),
    filter_status: Optional[int] = Query(None, alias="filter[status]", ge=0, le=1, description="按状态筛选"),
    language_id: Optional[int] = Query(None, ge=1, description="语言ID"),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("category:read")),
    service: CategoryService = Depends(get_service(CategoryService)),
):
    """
    获取分类列表
    
    - **skip**: 跳过的记录数
    - **limit**: 返回的记录数（最大100）
    - **sort**: 排序字段（sort_order）
    - **order**: 排序方向（asc, desc）
    - **filter[name]**: 按名称筛选（模糊匹配）
    - **filter[parent_id]**: 按父分类ID筛选
    - **filter[status]**: 按状态筛选
    - **language_id**: 语言ID
    """
    logger.info(f"开始获取分类列表: skip={skip}, limit={limit}, user_id={current_user.user_id}")
    try:
        result = await service.list_categories(
            skip, limit, sort, order, filter_name, filter_parent_id, filter_status, language_id
        )
        logger.info(f"分类列表获取完成: count={len(result)}")
        return result
    except Exception as e:
        logger.error(f"获取分类列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取分类列表失败: {str(e)}"
        )


@router.get("/{id}", response_model=CategoryResponse, summary="获取分类详情")
async def get_category(
    id: int,
    language_id: Optional[int] = Query(None, ge=1, description="语言ID"),
    include_children: bool = Query(False, description="是否包含子分类"),
    include_path: bool = Query(False, description="是否包含路径"),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("category:read")),
    service: CategoryService = Depends(get_service(CategoryService)),
):
    """
    获取分类详情
    
    - **id**: 分类ID
    - **language_id**: 语言ID
    - **include_children**: 是否包含子分类
    - **include_path**: 是否包含路径
    """
    logger.info(f"开始获取分类详情: id={id}, user_id={current_user.user_id}")
    try:
        response = await service.get_category(id, language_id, include_children, include_path)
        logger.info(f"分类详情获取完成: id={id}")
        return response
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.detail
        )
    except Exception as e:
        logger.error(f"获取分类详情失败: id={id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取分类详情失败: {str(e)}"
        )


@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED, summary="创建分类")
async def create_category(
    category_data: CategoryCreate,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("category:create")),
    service: CategoryService = Depends(get_service(CategoryService)),
):
    """
    创建新的分类
    
    - **parent_id**: 父分类ID（默认0，根分类）
    - **image**: 分类图片路径（可选）
    - **sort_order**: 排序
    - **status**: 状态（0=禁用，1=启用）
    - **descriptions**: 多语言描述数组（必填）
    """
    logger.info(f"开始创建分类: user_id={current_user.user_id}")
    try:
        response = await service.create_category(category_data)
        logger.info(f"分类创建完成: category_id={response.category_id}")
        return response
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.detail
        )
    except ConflictException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.detail
        )
    except Exception as e:
        logger.error(f"创建分类失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建分类失败: {str(e)}"
        )


@router.put("/{id}", response_model=CategoryResponse, summary="更新分类")
async def update_category(
    id: int,
    category_data: CategoryCreate,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("category:update")),
    service: CategoryService = Depends(get_service(CategoryService)),
):
    """
    完整更新分类
    
    - **id**: 分类ID
    - **parent_id**: 父分类ID
    - **image**: 分类图片路径
    - **sort_order**: 排序
    - **status**: 状态
    - **descriptions**: 多语言描述数组
    """
    logger.info(f"开始更新分类: id={id}, user_id={current_user.user_id}")
    try:
        response = await service.update_category(id, category_data)
        logger.info(f"分类更新完成: id={id}")
        return response
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.detail
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.detail
        )
    except Exception as e:
        logger.error(f"更新分类失败: id={id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新分类失败: {str(e)}"
        )


@router.patch("/{id}", response_model=CategoryResponse, summary="部分更新分类")
async def patch_category(
    id: int,
    category_data: CategoryUpdate,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("category:update")),
    service: CategoryService = Depends(get_service(CategoryService)),
):
    """
    部分更新分类
    
    - **id**: 分类ID
    - **parent_id**: 父分类ID（可选）
    - **image**: 分类图片路径（可选）
    - **sort_order**: 排序（可选）
    - **status**: 状态（可选）
    - **descriptions**: 多语言描述数组（可选）
    """
    logger.info(f"开始部分更新分类: id={id}, user_id={current_user.user_id}")
    try:
        response = await service.patch_category(id, category_data)
        logger.info(f"分类部分更新完成: id={id}")
        return response
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.detail
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.detail
        )
    except Exception as e:
        logger.error(f"部分更新分类失败: id={id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"部分更新分类失败: {str(e)}"
        )


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除分类")
async def delete_category(
    id: int,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("category:delete")),
    service: CategoryService = Depends(get_service(CategoryService)),
):
    """
    删除分类
    
    - **id**: 分类ID
    
    业务规则：如果分类下有子分类或商品，不允许删除
    """
    logger.info(f"开始删除分类: id={id}, user_id={current_user.user_id}")
    try:
        await service.delete_category(id)
        logger.info(f"分类删除完成: id={id}")
        return None
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.detail
        )
    except ConflictException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.detail
        )
    except Exception as e:
        logger.error(f"删除分类失败: id={id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除分类失败: {str(e)}"
        )


@router.patch("/{id}/move", response_model=CategoryResponse, summary="移动分类")
async def move_category(
    id: int,
    move_data: CategoryMoveRequest,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("category:update")),
    service: CategoryService = Depends(get_service(CategoryService)),
):
    """
    移动分类（改变父分类）
    
    - **id**: 分类ID
    - **parent_id**: 新的父分类ID
    
    业务规则：不能将分类移动到自己的子分类下（防止循环）
    """
    logger.info(f"开始移动分类: id={id}, new_parent_id={move_data.parent_id}, user_id={current_user.user_id}")
    try:
        response = await service.move_category(id, move_data.parent_id)
        logger.info(f"分类移动完成: id={id}, new_parent_id={move_data.parent_id}")
        return response
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.detail
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.detail
        )
    except Exception as e:
        logger.error(f"移动分类失败: id={id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"移动分类失败: {str(e)}"
        )


@router.patch("/{id}/sort", response_model=CategoryResponse, summary="更新分类排序")
async def update_category_sort(
    id: int,
    sort_order: int = Query(..., ge=0, description="新的排序值"),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("category:update")),
    service: CategoryService = Depends(get_service(CategoryService)),
):
    """
    更新分类排序
    
    - **id**: 分类ID
    - **sort_order**: 新的排序值
    """
    logger.info(f"开始更新分类排序: id={id}, sort_order={sort_order}, user_id={current_user.user_id}")
    try:
        response = await service.update_category_sort(id, sort_order)
        logger.info(f"分类排序更新完成: id={id}, sort_order={sort_order}")
        return response
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.detail
        )
    except Exception as e:
        logger.error(f"更新分类排序失败: id={id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新分类排序失败: {str(e)}"
        )


@router.get("/{id}/path", response_model=CategoryPathResponse, summary="获取分类路径")
async def get_category_path(
    id: int,
    language_id: Optional[int] = Query(None, ge=1, description="语言ID"),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("category:read")),
    service: CategoryService = Depends(get_service(CategoryService)),
):
    """
    获取分类的完整路径
    
    - **id**: 分类ID
    - **language_id**: 语言ID
    """
    logger.info(f"开始获取分类路径: id={id}, user_id={current_user.user_id}")
    try:
        response = await service.get_category_path(id, language_id)
        logger.info(f"分类路径获取完成: id={id}")
        return response
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.detail
        )
    except Exception as e:
        logger.error(f"获取分类路径失败: id={id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取分类路径失败: {str(e)}"
        )
