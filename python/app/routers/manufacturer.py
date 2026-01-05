"""
Manufacturer API router
"""
import logging
from fastapi import APIRouter, HTTPException, Query, status, Depends, Path, Body
from typing import List, Optional

try:
    from app.models.system.user import User
except (ImportError, AttributeError):
    import importlib
    user_module = importlib.import_module('app.models.system.user')
    User = user_module.User

from app.schemas.manufacturer import (
    ManufacturerCreate, ManufacturerUpdate, ManufacturerPatch, ManufacturerResponse,
    ManufacturerListItem, ManufacturerAutocompleteItem, ManufacturerBatchDeleteRequest,
    ManufacturerBatchDeleteResponse, ManufacturerStoreUpdateRequest, ManufacturerStoreUpdateResponse,
    ManufacturerSeoUrlUpdateRequest, ManufacturerSeoUrlUpdateResponse,
    ManufacturerLayoutUpdateRequest, ManufacturerLayoutUpdateResponse, ProductListItem,
    SeoUrlItem, LayoutItem, ManufacturerStoreItem
)
from app.services.manufacturer_service import ManufacturerService
from app.exceptions import NotFoundException, ConflictException, ValidationException
from app.api.deps import get_current_user, require_permission, get_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/manufacturers", tags=["manufacturers"])


@router.get("/", response_model=List[ManufacturerListItem], summary="获取制造商列表")
async def list_manufacturers(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(20, ge=1, le=100, description="返回的记录数"),
    sort: str = Query("name", description="排序字段（name, sort_order）"),
    order: str = Query("asc", description="排序方向（asc, desc）"),
    filter_name: Optional[str] = Query(None, alias="filter[name]", description="按名称筛选（模糊匹配）"),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("manufacturer:read")),
    service: ManufacturerService = Depends(get_service(ManufacturerService)),
):
    """
    获取制造商列表
    
    - **skip**: 跳过的记录数
    - **limit**: 返回的记录数（最大100）
    - **sort**: 排序字段（name, sort_order）
    - **order**: 排序方向（asc, desc）
    - **filter[name]**: 按名称筛选（模糊匹配，不区分大小写）
    """
    logger.info(f"开始获取制造商列表: skip={skip}, limit={limit}, user_id={current_user.user_id}")
    try:
        result = await service.list_manufacturers(skip, limit, sort, order, filter_name)
        logger.info(f"制造商列表获取完成: count={len(result)}")
        return result
    except Exception as e:
        logger.error(f"获取制造商列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取制造商列表失败: {str(e)}"
        )


@router.get("/autocomplete", response_model=List[ManufacturerAutocompleteItem], summary="自动完成制造商名称")
async def autocomplete_manufacturers(
    filter_name: str = Query(..., min_length=1, description="名称筛选（模糊匹配）"),
    limit: int = Query(10, ge=1, le=50, description="返回的记录数（最大50）"),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("manufacturer:read")),
    service: ManufacturerService = Depends(get_service(ManufacturerService)),
):
    """
    自动完成制造商名称
    
    - **filter_name**: 名称筛选（模糊匹配）
    - **limit**: 返回的记录数（最大50）
    """
    logger.info(f"开始自动完成制造商: filter_name={filter_name}, user_id={current_user.user_id}")
    try:
        result = await service.autocomplete_manufacturers(filter_name, limit)
        logger.info(f"自动完成制造商完成: count={len(result)}")
        return result
    except Exception as e:
        logger.error(f"自动完成制造商失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"自动完成制造商失败: {str(e)}"
        )


@router.get("/{id}", response_model=ManufacturerResponse, summary="获取制造商详情")
async def get_manufacturer(
    id: int = Path(..., ge=1, description="制造商ID"),
    include_stores: bool = Query(True, description="是否包含店铺关联"),
    include_layouts: bool = Query(True, description="是否包含布局关联"),
    include_seo_urls: bool = Query(True, description="是否包含SEO URL"),
    include_product_count: bool = Query(True, description="是否包含商品数量"),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("manufacturer:read")),
    service: ManufacturerService = Depends(get_service(ManufacturerService)),
):
    """
    获取制造商详情
    
    - **id**: 制造商ID
    - **include_stores**: 是否包含店铺关联
    - **include_layouts**: 是否包含布局关联
    - **include_seo_urls**: 是否包含SEO URL
    - **include_product_count**: 是否包含商品数量
    """
    logger.info(f"开始获取制造商详情: id={id}, user_id={current_user.user_id}")
    try:
        result = await service.get_manufacturer(id, include_stores, include_layouts, include_seo_urls, include_product_count)
        logger.info(f"制造商详情获取完成: id={id}")
        return result
    except NotFoundException as e:
        logger.warning(f"制造商不存在: id={id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.detail
        )
    except Exception as e:
        logger.error(f"获取制造商详情失败: id={id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取制造商详情失败: {str(e)}"
        )


@router.post("/", response_model=ManufacturerResponse, status_code=status.HTTP_201_CREATED, summary="创建制造商")
async def create_manufacturer(
    data: ManufacturerCreate,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("manufacturer:create")),
    service: ManufacturerService = Depends(get_service(ManufacturerService)),
):
    """
    创建制造商
    
    - **name**: 制造商名称（必需，1-64字符）
    - **image**: 制造商图片路径（可选）
    - **sort_order**: 排序顺序（可选，默认0）
    - **manufacturer_store**: 店铺ID数组（可选，默认[0]）
    - **manufacturer_seo_url**: SEO URL对象（可选）
    - **manufacturer_layout**: 布局对象（可选）
    """
    logger.info(f"开始创建制造商: name={data.name}, user_id={current_user.user_id}")
    try:
        result = await service.create_manufacturer(data)
        logger.info(f"制造商创建完成: manufacturer_id={result.manufacturer_id}")
        return result
    except ConflictException as e:
        logger.warning(f"创建制造商失败: name={data.name}, error={str(e.detail)}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.detail
        )
    except ValidationException as e:
        logger.warning(f"创建制造商验证失败: name={data.name}, error={str(e.detail)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.detail
        )
    except Exception as e:
        logger.error(f"创建制造商失败: name={data.name}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建制造商失败: {str(e)}"
        )


@router.put("/{id}", response_model=ManufacturerResponse, summary="更新制造商")
async def update_manufacturer(
    id: int = Path(..., ge=1, description="制造商ID"),
    data: ManufacturerUpdate = Body(...),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("manufacturer:update")),
    service: ManufacturerService = Depends(get_service(ManufacturerService)),
):
    """
    更新制造商（完整更新）
    
    - **id**: 制造商ID
    - 请求体：制造商更新数据（所有字段都是可选的）
    """
    logger.info(f"开始更新制造商: id={id}, user_id={current_user.user_id}")
    try:
        result = await service.update_manufacturer(id, data)
        logger.info(f"制造商更新完成: id={id}")
        return result
    except NotFoundException as e:
        logger.warning(f"制造商不存在: id={id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.detail
        )
    except ConflictException as e:
        logger.warning(f"更新制造商失败: id={id}, error={str(e.detail)}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.detail
        )
    except ValidationException as e:
        logger.warning(f"更新制造商验证失败: id={id}, error={str(e.detail)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.detail
        )
    except Exception as e:
        logger.error(f"更新制造商失败: id={id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新制造商失败: {str(e)}"
        )


@router.patch("/{id}", response_model=ManufacturerResponse, summary="部分更新制造商")
async def patch_manufacturer(
    id: int = Path(..., ge=1, description="制造商ID"),
    data: ManufacturerPatch = Body(...),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("manufacturer:update")),
    service: ManufacturerService = Depends(get_service(ManufacturerService)),
):
    """
    部分更新制造商
    
    - **id**: 制造商ID
    - 请求体：只需提供要更新的字段
    """
    logger.info(f"开始部分更新制造商: id={id}, user_id={current_user.user_id}")
    try:
        result = await service.patch_manufacturer(id, data)
        logger.info(f"制造商部分更新完成: id={id}")
        return result
    except NotFoundException as e:
        logger.warning(f"制造商不存在: id={id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.detail
        )
    except ConflictException as e:
        logger.warning(f"部分更新制造商失败: id={id}, error={str(e.detail)}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.detail
        )
    except ValidationException as e:
        logger.warning(f"部分更新制造商验证失败: id={id}, error={str(e.detail)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.detail
        )
    except Exception as e:
        logger.error(f"部分更新制造商失败: id={id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"部分更新制造商失败: {str(e)}"
        )


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除制造商")
async def delete_manufacturer(
    id: int = Path(..., ge=1, description="制造商ID"),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("manufacturer:delete")),
    service: ManufacturerService = Depends(get_service(ManufacturerService)),
):
    """
    删除制造商
    
    - **id**: 制造商ID
    - 如果有关联商品，将返回错误
    """
    logger.info(f"开始删除制造商: id={id}, user_id={current_user.user_id}")
    try:
        await service.delete_manufacturer(id)
        logger.info(f"制造商删除完成: id={id}")
    except NotFoundException as e:
        logger.warning(f"制造商不存在: id={id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.detail
        )
    except ConflictException as e:
        logger.warning(f"删除制造商失败: id={id}, error={str(e.detail)}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.detail
        )
    except Exception as e:
        logger.error(f"删除制造商失败: id={id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除制造商失败: {str(e)}"
        )


@router.delete("/", response_model=ManufacturerBatchDeleteResponse, summary="批量删除制造商")
async def batch_delete_manufacturers(
    request: ManufacturerBatchDeleteRequest = Body(...),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("manufacturer:delete")),
    service: ManufacturerService = Depends(get_service(ManufacturerService)),
):
    """
    批量删除制造商
    
    - **ids**: 制造商ID数组
    - 只删除没有商品关联的制造商
    - 返回成功和失败的详细信息
    """
    logger.info(f"开始批量删除制造商: ids={request.ids}, user_id={current_user.user_id}")
    try:
        result = await service.batch_delete_manufacturers(request)
        logger.info(f"批量删除制造商完成: deleted={result.deleted}, failed={result.failed}")
        return result
    except Exception as e:
        logger.error(f"批量删除制造商失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量删除制造商失败: {str(e)}"
        )


# ==================== 店铺关联接口 ====================

@router.get("/{id}/stores", response_model=List[ManufacturerStoreItem], summary="获取制造商的店铺关联")
async def get_manufacturer_stores(
    id: int = Path(..., ge=1, description="制造商ID"),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("manufacturer:read")),
    service: ManufacturerService = Depends(get_service(ManufacturerService)),
):
    """
    获取制造商的店铺关联列表
    
    - **id**: 制造商ID
    """
    logger.info(f"开始获取制造商店铺关联: id={id}, user_id={current_user.user_id}")
    try:
        result = await service.get_manufacturer_stores(id)
        logger.info(f"制造商店铺关联获取完成: id={id}, count={len(result)}")
        return result
    except NotFoundException as e:
        logger.warning(f"制造商不存在: id={id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.detail
        )
    except Exception as e:
        logger.error(f"获取制造商店铺关联失败: id={id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取制造商店铺关联失败: {str(e)}"
        )


@router.post("/{id}/stores", response_model=ManufacturerStoreUpdateResponse, summary="批量更新制造商的店铺关联")
async def update_manufacturer_stores(
    id: int = Path(..., ge=1, description="制造商ID"),
    request: ManufacturerStoreUpdateRequest = Body(...),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("manufacturer:update")),
    service: ManufacturerService = Depends(get_service(ManufacturerService)),
):
    """
    批量更新制造商的店铺关联
    
    - **id**: 制造商ID
    - **store_ids**: 店铺ID数组
    - 会替换制造商的所有店铺关联
    """
    logger.info(f"开始更新制造商店铺关联: id={id}, user_id={current_user.user_id}")
    try:
        result = await service.update_manufacturer_stores(id, request)
        logger.info(f"制造商店铺关联更新完成: id={id}, added={result.added}, removed={result.removed}")
        return result
    except NotFoundException as e:
        logger.warning(f"制造商不存在: id={id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.detail
        )
    except ValidationException as e:
        logger.warning(f"更新制造商店铺关联验证失败: id={id}, error={str(e.detail)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.detail
        )
    except Exception as e:
        logger.error(f"更新制造商店铺关联失败: id={id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新制造商店铺关联失败: {str(e)}"
        )


# ==================== SEO URL接口 ====================

@router.get("/{id}/seo-urls", response_model=List[SeoUrlItem], summary="获取制造商的SEO URL列表")
async def get_manufacturer_seo_urls(
    id: int = Path(..., ge=1, description="制造商ID"),
    store_id: Optional[int] = Query(None, ge=0, description="店铺ID筛选"),
    language_id: Optional[int] = Query(None, ge=1, description="语言ID筛选"),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("manufacturer:read")),
    service: ManufacturerService = Depends(get_service(ManufacturerService)),
):
    """
    获取制造商的SEO URL列表
    
    - **id**: 制造商ID
    - **store_id**: 店铺ID筛选（可选）
    - **language_id**: 语言ID筛选（可选）
    """
    logger.info(f"开始获取制造商SEO URL: id={id}, user_id={current_user.user_id}")
    try:
        result = await service.get_manufacturer_seo_urls(id, store_id, language_id)
        logger.info(f"制造商SEO URL获取完成: id={id}, count={len(result)}")
        return result
    except NotFoundException as e:
        logger.warning(f"制造商不存在: id={id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.detail
        )
    except Exception as e:
        logger.error(f"获取制造商SEO URL失败: id={id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取制造商SEO URL失败: {str(e)}"
        )


@router.post("/{id}/seo-urls", response_model=ManufacturerSeoUrlUpdateResponse, summary="批量更新制造商的SEO URL")
async def update_manufacturer_seo_urls(
    id: int = Path(..., ge=1, description="制造商ID"),
    request: ManufacturerSeoUrlUpdateRequest = Body(...),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("manufacturer:update")),
    service: ManufacturerService = Depends(get_service(ManufacturerService)),
):
    """
    批量更新制造商的SEO URL
    
    - **id**: 制造商ID
    - **seo_urls**: SEO URL对象，格式：{store_id: {language_id: keyword}}
    - 会替换制造商的所有SEO URL
    - 关键字必须唯一（在同一店铺和语言下）
    """
    logger.info(f"开始更新制造商SEO URL: id={id}, user_id={current_user.user_id}")
    try:
        result = await service.update_manufacturer_seo_urls(id, request)
        logger.info(f"制造商SEO URL更新完成: id={id}, total={result.total}")
        return result
    except NotFoundException as e:
        logger.warning(f"制造商不存在: id={id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.detail
        )
    except ValidationException as e:
        logger.warning(f"更新制造商SEO URL验证失败: id={id}, error={str(e.detail)}")
        # SEO URL验证错误：关键字长度超限返回422，其他（重复关键字、格式错误）返回400
        error_detail = str(e.detail) if isinstance(e.detail, dict) else e.detail
        if "长度" in str(error_detail) or "长度必须在" in str(error_detail):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=e.detail
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=e.detail
            )
    except Exception as e:
        logger.error(f"更新制造商SEO URL失败: id={id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新制造商SEO URL失败: {str(e)}"
        )


# ==================== 布局接口 ====================

@router.get("/{id}/layouts", response_model=List[LayoutItem], summary="获取制造商的布局列表")
async def get_manufacturer_layouts(
    id: int = Path(..., ge=1, description="制造商ID"),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("manufacturer:read")),
    service: ManufacturerService = Depends(get_service(ManufacturerService)),
):
    """
    获取制造商的布局列表
    
    - **id**: 制造商ID
    """
    logger.info(f"开始获取制造商布局: id={id}, user_id={current_user.user_id}")
    try:
        result = await service.get_manufacturer_layouts(id)
        logger.info(f"制造商布局获取完成: id={id}, count={len(result)}")
        return result
    except NotFoundException as e:
        logger.warning(f"制造商不存在: id={id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.detail
        )
    except Exception as e:
        logger.error(f"获取制造商布局失败: id={id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取制造商布局失败: {str(e)}"
        )


@router.post("/{id}/layouts", response_model=ManufacturerLayoutUpdateResponse, summary="批量更新制造商的布局")
async def update_manufacturer_layouts(
    id: int = Path(..., ge=1, description="制造商ID"),
    request: ManufacturerLayoutUpdateRequest = Body(...),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("manufacturer:update")),
    service: ManufacturerService = Depends(get_service(ManufacturerService)),
):
    """
    批量更新制造商的布局
    
    - **id**: 制造商ID
    - **layouts**: 布局对象，格式：{store_id: layout_id}
    - 会替换制造商的所有布局关联
    - 如果layout_id为0或null，表示删除该店铺的布局关联
    """
    logger.info(f"开始更新制造商布局: id={id}, user_id={current_user.user_id}")
    try:
        result = await service.update_manufacturer_layouts(id, request)
        logger.info(f"制造商布局更新完成: id={id}, total={result.total}")
        return result
    except NotFoundException as e:
        logger.warning(f"制造商不存在: id={id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.detail
        )
    except ValidationException as e:
        logger.warning(f"更新制造商布局验证失败: id={id}, error={str(e.detail)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.detail
        )
    except Exception as e:
        logger.error(f"更新制造商布局失败: id={id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新制造商布局失败: {str(e)}"
        )


# ==================== 商品列表接口 ====================

@router.get("/{id}/products", response_model=List[ProductListItem], summary="获取制造商下的商品列表")
async def get_manufacturer_products(
    id: int = Path(..., ge=1, description="制造商ID"),
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(20, ge=1, le=100, description="返回的记录数"),
    sort: str = Query("sort_order", description="排序字段（name, price, sort_order, date_added）"),
    order: str = Query("asc", description="排序方向（asc, desc）"),
    product_status: Optional[int] = Query(None, ge=0, le=1, alias="status", description="商品状态筛选（0=禁用，1=启用）"),
    language_id: Optional[int] = Query(None, ge=1, description="语言ID（用于返回对应语言的商品名称）"),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("manufacturer:read")),
    service: ManufacturerService = Depends(get_service(ManufacturerService)),
):
    """
    获取制造商下的商品列表
    
    - **id**: 制造商ID
    - **skip**: 跳过的记录数
    - **limit**: 返回的记录数（最大100）
    - **sort**: 排序字段（name, price, sort_order, date_added）
    - **order**: 排序方向（asc, desc）
    - **status**: 商品状态筛选（0=禁用，1=启用）
    - **language_id**: 语言ID（用于返回对应语言的商品名称）
    """
    logger.info(f"开始获取制造商商品列表: id={id}, user_id={current_user.user_id}")
    try:
        result = await service.get_manufacturer_products(id, skip, limit, sort, order, product_status, language_id)
        logger.info(f"制造商商品列表获取完成: id={id}, count={len(result)}")
        return result
    except NotFoundException as e:
        logger.warning(f"制造商不存在: id={id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.detail
        )
    except Exception as e:
        logger.error(f"获取制造商商品列表失败: id={id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取制造商商品列表失败: {str(e)}"
        )

