"""
Product API router
"""
import logging
from fastapi import APIRouter, HTTPException, Query, Path, Body, status, Depends
from typing import List, Optional

try:
    from app.models.system.user import User
except (ImportError, AttributeError):
    import importlib
    user_module = importlib.import_module('app.models.system.user')
    User = user_module.User

from app.schemas.product import (
    ProductCreate, ProductUpdate, ProductResponse, ProductListItem,
    ProductFilterParams, ProductCopyRequest,
    ProductAttributeCreate, ProductAttributeResponse,
    ProductOptionCreate, ProductOptionResponse, ProductOptionValueCreate, ProductOptionValueResponse,
    ProductImageCreate, ProductImageResponse,
    ProductCategoryResponse
)
from app.services.product_service import ProductService
from app.services.product_attribute_service import ProductAttributeService
from app.services.product_option_service import ProductOptionService
from app.services.product_image_service import ProductImageService
from app.services.product_category_service import ProductCategoryService
from app.exceptions import NotFoundException, ConflictException, ValidationException
from app.api.deps import get_current_user, require_permission, get_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/products", tags=["products"])


@router.get("/", response_model=List[ProductListItem], summary="获取商品列表")
async def list_products(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(20, ge=1, le=100, description="返回的记录数"),
    sort: str = Query("sort_order", description="排序字段"),
    order: str = Query("asc", description="排序方向"),
    filter_name: Optional[str] = Query(None, alias="filter[name]", description="按商品名称筛选（模糊匹配）"),
    filter_model: Optional[str] = Query(None, alias="filter[model]", description="按商品型号筛选（模糊匹配）"),
    filter_category_id: Optional[int] = Query(None, alias="filter[category_id]", ge=1, description="按分类ID筛选"),
    filter_manufacturer_id: Optional[int] = Query(None, alias="filter[manufacturer_id]", ge=1, description="按制造商ID筛选"),
    filter_price_from: Optional[float] = Query(None, alias="filter[price_from]", ge=0, description="最低价格"),
    filter_price_to: Optional[float] = Query(None, alias="filter[price_to]", ge=0, description="最高价格"),
    filter_quantity_from: Optional[int] = Query(None, alias="filter[quantity_from]", ge=0, description="最低库存"),
    filter_quantity_to: Optional[int] = Query(None, alias="filter[quantity_to]", ge=0, description="最高库存"),
    filter_status: Optional[int] = Query(None, alias="filter[status]", ge=0, le=1, description="状态筛选（0=禁用，1=启用）"),
    filter_master_id: Optional[int] = Query(None, alias="filter[master_id]", ge=0, description="主商品ID（用于查询变体商品）"),
    language_id: Optional[int] = Query(None, ge=1, description="语言ID"),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("product:read")),
    service: ProductService = Depends(get_service(ProductService)),
):
    """
    获取商品列表
    
    - **skip**: 跳过的记录数
    - **limit**: 返回的记录数（最大100）
    - **sort**: 排序字段（name, model, price, quantity, status, sort_order, date_added, date_modified）
    - **order**: 排序方向（asc, desc）
    - **filter[name]**: 按商品名称筛选（模糊匹配）
    - **filter[model]**: 按商品型号筛选（模糊匹配）
    - **filter[category_id]**: 按分类ID筛选
    - **filter[manufacturer_id]**: 按制造商ID筛选
    - **filter[price_from]**: 最低价格
    - **filter[price_to]**: 最高价格
    - **filter[quantity_from]**: 最低库存
    - **filter[quantity_to]**: 最高库存
    - **filter[status]**: 状态筛选（0=禁用，1=启用）
    - **filter[master_id]**: 主商品ID（用于查询变体商品）
    - **language_id**: 语言ID
    """
    logger.info(f"开始获取商品列表: skip={skip}, limit={limit}, user_id={current_user.user_id}")
    try:
        # 构建筛选参数
        filter_params = ProductFilterParams(
            name=filter_name,
            model=filter_model,
            category_id=filter_category_id,
            manufacturer_id=filter_manufacturer_id,
            price_from=filter_price_from,
            price_to=filter_price_to,
            quantity_from=filter_quantity_from,
            quantity_to=filter_quantity_to,
            status=filter_status,
            master_id=filter_master_id
        )
        
        result = await service.list_products(
            skip=skip,
            limit=limit,
            sort=sort,
            order=order,
            filter_params=filter_params,
            language_id=language_id
        )
        logger.info(f"商品列表获取完成: count={len(result)}")
        return result
    except Exception as e:
        logger.error(f"获取商品列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取商品列表失败: {str(e)}"
        )


@router.get("/{id}", response_model=ProductResponse, summary="获取商品详情")
async def get_product(
    id: int = Path(..., ge=1, description="商品ID"),
    language_id: Optional[int] = Query(None, ge=1, description="语言ID"),
    include: Optional[str] = Query(None, description="包含的关联数据，多个用逗号分隔（attributes,options,images,categories,related）"),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("product:read")),
    service: ProductService = Depends(get_service(ProductService)),
):
    """
    获取商品详情
    
    - **id**: 商品ID
    - **language_id**: 语言ID
    - **include**: 包含的关联数据，多个用逗号分隔（attributes,options,images,categories,related）
    """
    logger.info(f"开始获取商品详情: id={id}, include={include}, user_id={current_user.user_id}")
    try:
        # 解析include参数
        include_attributes = False
        include_options = False
        include_images = False
        include_categories = False
        include_related = False
        
        if include:
            include_list = [item.strip().lower() for item in include.split(',')]
            include_attributes = 'attributes' in include_list
            include_options = 'options' in include_list
            include_images = 'images' in include_list
            include_categories = 'categories' in include_list
            include_related = 'related' in include_list
        
        response = await service.get_product(
            product_id=id,
            language_id=language_id,
            include_attributes=include_attributes,
            include_options=include_options,
            include_images=include_images,
            include_categories=include_categories,
            include_related=include_related
        )
        logger.info(f"商品详情获取完成: id={id}")
        return response
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.detail
        )
    except Exception as e:
        logger.error(f"获取商品详情失败: id={id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取商品详情失败: {str(e)}"
        )


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED, summary="创建商品")
async def create_product(
    product_data: ProductCreate,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("product:create")),
    service: ProductService = Depends(get_service(ProductService)),
):
    """
    创建新商品
    
    - **master_id**: 主商品ID（0表示主商品，>0表示变体商品）
    - **model**: 商品型号（必填）
    - **sku**: 商品SKU（可选）
    - **price**: 商品价格（必填）
    - **quantity**: 库存数量（默认0）
    - **descriptions**: 多语言描述数组（必填，至少一个）
    - **attributes**: 商品属性数组（可选）
    - **options**: 商品选项数组（可选）
    - **images**: 商品图片数组（可选）
    - **category_ids**: 分类ID数组（可选）
    - **related_product_ids**: 相关商品ID数组（可选）
    """
    logger.info(f"开始创建商品: user_id={current_user.user_id}")
    try:
        response = await service.create_product(product_data)
        logger.info(f"商品创建完成: product_id={response.product_id}")
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
        logger.error(f"创建商品失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建商品失败: {str(e)}"
        )


@router.put("/{id}", response_model=ProductResponse, summary="更新商品")
async def update_product(
    id: int,
    product_data: ProductUpdate,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("product:update")),
    service: ProductService = Depends(get_service(ProductService)),
):
    """
    完整更新商品
    
    - **id**: 商品ID
    - **master_id**: 主商品ID
    - **model**: 商品型号
    - **sku**: 商品SKU
    - **price**: 商品价格
    - **quantity**: 库存数量
    - **descriptions**: 多语言描述数组
    - **attributes**: 商品属性数组
    - **options**: 商品选项数组
    - **images**: 商品图片数组
    - **category_ids**: 分类ID数组
    - **related_product_ids**: 相关商品ID数组
    """
    logger.info(f"开始更新商品: id={id}, user_id={current_user.user_id}")
    try:
        response = await service.update_product(id, product_data)
        logger.info(f"商品更新完成: id={id}")
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
    except ConflictException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.detail
        )
    except Exception as e:
        logger.error(f"更新商品失败: id={id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新商品失败: {str(e)}"
        )


@router.patch("/{id}", response_model=ProductResponse, summary="部分更新商品")
async def patch_product(
    id: int,
    product_data: ProductUpdate,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("product:update")),
    service: ProductService = Depends(get_service(ProductService)),
):
    """
    部分更新商品
    
    - **id**: 商品ID
    - **model**: 商品型号（可选）
    - **sku**: 商品SKU（可选）
    - **price**: 商品价格（可选）
    - **quantity**: 库存数量（可选）
    - **descriptions**: 多语言描述数组（可选）
    - **attributes**: 商品属性数组（可选）
    - **options**: 商品选项数组（可选）
    - **images**: 商品图片数组（可选）
    - **category_ids**: 分类ID数组（可选）
    - **related_product_ids**: 相关商品ID数组（可选）
    """
    logger.info(f"开始部分更新商品: id={id}, user_id={current_user.user_id}")
    try:
        # 将ProductUpdate转换为字典（Pydantic的dict()方法）
        update_data = product_data.model_dump(exclude_unset=True)
        response = await service.patch_product(id, update_data)
        logger.info(f"商品部分更新完成: id={id}")
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
    except ConflictException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.detail
        )
    except Exception as e:
        logger.error(f"部分更新商品失败: id={id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"部分更新商品失败: {str(e)}"
        )


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除商品")
async def delete_product(
    id: int,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("product:delete")),
    service: ProductService = Depends(get_service(ProductService)),
):
    """
    删除商品
    
    - **id**: 商品ID
    
    注意：删除商品前会检查关联数据（变体商品、订单、购物车），如果存在关联则不允许删除
    """
    logger.info(f"开始删除商品: id={id}, user_id={current_user.user_id}")
    try:
        await service.delete_product(id)
        logger.info(f"商品删除完成: id={id}")
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
        logger.error(f"删除商品失败: id={id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除商品失败: {str(e)}"
        )


@router.post("/{id}/copy", response_model=ProductResponse, status_code=status.HTTP_201_CREATED, summary="复制商品")
async def copy_product(
    id: int,
    copy_request: ProductCopyRequest = ProductCopyRequest(),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("product:create")),
    service: ProductService = Depends(get_service(ProductService)),
):
    """
    复制商品
    
    - **id**: 要复制的商品ID
    - **name_suffix**: 名称后缀（可选，默认"Copy"）
    - **copy_attributes**: 是否复制属性（默认true）
    - **copy_options**: 是否复制选项（默认true）
    - **copy_images**: 是否复制图片（默认true）
    - **copy_categories**: 是否复制分类（默认true）
    - **copy_related**: 是否复制相关商品（默认true）
    
    注意：复制商品时会清除唯一标识（sku, upc, rating等），并重置状态为禁用
    """
    logger.info(f"开始复制商品: id={id}, user_id={current_user.user_id}")
    try:
        response = await service.copy_product(id, copy_request)
        logger.info(f"商品复制完成: source_id={id}, new_product_id={response.product_id}")
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
        logger.error(f"复制商品失败: id={id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"复制商品失败: {str(e)}"
        )


# ==================== 商品属性关联路由 ====================

@router.get("/{product_id}/attributes", response_model=List[ProductAttributeResponse], summary="获取商品属性列表")
async def list_product_attributes(
    product_id: int,
    language_id: Optional[int] = Query(None, ge=1, description="语言ID"),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("product:read")),
    service: ProductAttributeService = Depends(get_service(ProductAttributeService)),
):
    """获取商品的所有属性"""
    logger.info(f"开始获取商品属性列表: product_id={product_id}, user_id={current_user.user_id}")
    try:
        return await service.list_product_attributes(product_id, language_id)
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.detail)
    except Exception as e:
        logger.error(f"获取商品属性列表失败: product_id={product_id}, error={str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取商品属性列表失败: {str(e)}")


@router.post("/{product_id}/attributes", status_code=status.HTTP_201_CREATED, summary="添加商品属性")
async def add_product_attribute(
    product_id: int,
    attribute_data: ProductAttributeCreate,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("product:update")),
    service: ProductAttributeService = Depends(get_service(ProductAttributeService)),
):
    """为商品添加属性（支持多语言）"""
    logger.info(f"开始添加商品属性: product_id={product_id}, user_id={current_user.user_id}")
    try:
        # 循环处理每个语言的描述
        for desc in attribute_data.descriptions:
            await service.add_product_attribute(
                product_id=product_id,
                attribute_id=attribute_data.attribute_id,
                language_id=desc.language_id,
                text=desc.text
            )
        logger.info(f"商品属性添加完成: product_id={product_id}, attribute_id={attribute_data.attribute_id}")
        return {"message": "商品属性添加成功"}
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.detail)
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.detail)
    except Exception as e:
        logger.error(f"添加商品属性失败: product_id={product_id}, error={str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"添加商品属性失败: {str(e)}")


@router.put("/{product_id}/attributes/{attribute_id}", summary="更新商品属性")
async def update_product_attribute(
    product_id: int,
    attribute_id: int,
    attribute_data: ProductAttributeCreate,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("product:update")),
    service: ProductAttributeService = Depends(get_service(ProductAttributeService)),
):
    """更新商品属性（先删除再添加所有语言）"""
    logger.info(f"开始更新商品属性: product_id={product_id}, attribute_id={attribute_id}, user_id={current_user.user_id}")
    try:
        descriptions = [{"language_id": desc.language_id, "text": desc.text} for desc in attribute_data.descriptions]
        await service.update_product_attribute(product_id, attribute_id, descriptions)
        logger.info(f"商品属性更新完成: product_id={product_id}, attribute_id={attribute_id}")
        return {"message": "商品属性更新成功"}
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.detail)
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.detail)
    except Exception as e:
        logger.error(f"更新商品属性失败: product_id={product_id}, attribute_id={attribute_id}, error={str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"更新商品属性失败: {str(e)}")


@router.delete("/{product_id}/attributes/{attribute_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除商品属性")
async def delete_product_attribute(
    product_id: int,
    attribute_id: int,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("product:update")),
    service: ProductAttributeService = Depends(get_service(ProductAttributeService)),
):
    """删除商品属性（删除该属性的所有语言记录）"""
    logger.info(f"开始删除商品属性: product_id={product_id}, attribute_id={attribute_id}, user_id={current_user.user_id}")
    try:
        await service.delete_product_attribute(product_id, attribute_id)
        logger.info(f"商品属性删除完成: product_id={product_id}, attribute_id={attribute_id}")
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.detail)
    except Exception as e:
        logger.error(f"删除商品属性失败: product_id={product_id}, attribute_id={attribute_id}, error={str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"删除商品属性失败: {str(e)}")


@router.patch("/{product_id}/attributes", summary="批量更新商品属性")
async def batch_update_product_attributes(
    product_id: int,
    attributes: List[ProductAttributeCreate],
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("product:update")),
    service: ProductAttributeService = Depends(get_service(ProductAttributeService)),
):
    """批量更新商品属性（先删除所有再批量添加）"""
    logger.info(f"开始批量更新商品属性: product_id={product_id}, user_id={current_user.user_id}")
    try:
        await service.batch_update_product_attributes(product_id, attributes)
        logger.info(f"商品属性批量更新完成: product_id={product_id}")
        return {"message": "商品属性批量更新成功"}
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.detail)
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.detail)
    except Exception as e:
        logger.error(f"批量更新商品属性失败: product_id={product_id}, error={str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"批量更新商品属性失败: {str(e)}")


# ==================== 商品选项关联路由 ====================

@router.get("/{product_id}/options", response_model=List[ProductOptionResponse], summary="获取商品选项列表")
async def list_product_options(
    product_id: int,
    language_id: Optional[int] = Query(None, ge=1, description="语言ID"),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("product:read")),
    service: ProductOptionService = Depends(get_service(ProductOptionService)),
):
    """获取商品的所有选项"""
    logger.info(f"开始获取商品选项列表: product_id={product_id}, user_id={current_user.user_id}")
    try:
        return await service.list_product_options(product_id, language_id)
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.detail)
    except Exception as e:
        logger.error(f"获取商品选项列表失败: product_id={product_id}, error={str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取商品选项列表失败: {str(e)}")


@router.post("/{product_id}/options", status_code=status.HTTP_201_CREATED, summary="添加商品选项")
async def add_product_option(
    product_id: int,
    option_data: ProductOptionCreate,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("product:update")),
    service: ProductOptionService = Depends(get_service(ProductOptionService)),
):
    """为商品添加选项"""
    logger.info(f"开始添加商品选项: product_id={product_id}, user_id={current_user.user_id}")
    try:
        product_option_id = await service.add_product_option(product_id, option_data)
        logger.info(f"商品选项添加完成: product_id={product_id}, product_option_id={product_option_id}")
        return {"product_option_id": product_option_id, "message": "商品选项添加成功"}
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.detail)
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.detail)
    except Exception as e:
        logger.error(f"添加商品选项失败: product_id={product_id}, error={str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"添加商品选项失败: {str(e)}")


@router.delete("/{product_id}/options/{product_option_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除商品选项")
async def delete_product_option(
    product_id: int,
    product_option_id: int,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("product:update")),
    service: ProductOptionService = Depends(get_service(ProductOptionService)),
):
    """删除商品选项"""
    logger.info(f"开始删除商品选项: product_id={product_id}, product_option_id={product_option_id}, user_id={current_user.user_id}")
    try:
        await service.delete_product_option(product_id, product_option_id)
        logger.info(f"商品选项删除完成: product_id={product_id}, product_option_id={product_option_id}")
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.detail)
    except ConflictException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.detail)
    except Exception as e:
        logger.error(f"删除商品选项失败: product_id={product_id}, product_option_id={product_option_id}, error={str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"删除商品选项失败: {str(e)}")


@router.get("/{product_id}/options/{product_option_id}/values", response_model=List[ProductOptionValueResponse], summary="获取选项值列表")
async def list_product_option_values(
    product_id: int,
    product_option_id: int,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("product:read")),
    service: ProductOptionService = Depends(get_service(ProductOptionService)),
):
    """获取选项的所有值"""
    logger.info(f"开始获取选项值列表: product_id={product_id}, product_option_id={product_option_id}, user_id={current_user.user_id}")
    try:
        return await service.list_product_option_values(product_id, product_option_id)
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.detail)
    except Exception as e:
        logger.error(f"获取选项值列表失败: product_id={product_id}, product_option_id={product_option_id}, error={str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取选项值列表失败: {str(e)}")


@router.post("/{product_id}/options/{product_option_id}/values", status_code=status.HTTP_201_CREATED, summary="添加选项值")
async def add_product_option_value(
    product_id: int,
    product_option_id: int,
    option_value_data: ProductOptionValueCreate,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("product:update")),
    service: ProductOptionService = Depends(get_service(ProductOptionService)),
):
    """为选项添加值"""
    logger.info(f"开始添加选项值: product_id={product_id}, product_option_id={product_option_id}, user_id={current_user.user_id}")
    try:
        # 需要先获取product_option以获取option_id
        from app.models.catalog.product_option import ProductOption
        product_option = await ProductOption.get_or_none(product_option_id=product_option_id)
        if not product_option:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="商品选项不存在")
        
        product_option_value_id = await service.add_product_option_value(
            product_id, product_option_id, product_option.option_id, option_value_data
        )
        logger.info(f"选项值添加完成: product_id={product_id}, product_option_id={product_option_id}, product_option_value_id={product_option_value_id}")
        return {"product_option_value_id": product_option_value_id, "message": "选项值添加成功"}
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.detail)
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.detail)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"添加选项值失败: product_id={product_id}, product_option_id={product_option_id}, error={str(e)}")
        # 如果错误信息中包含404，说明是NotFoundException被转换为HTTPException
        if "404" in str(e) or "不存在" in str(e):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"添加选项值失败: {str(e)}")


# ==================== 商品图片管理路由 ====================

@router.get("/{product_id}/images", response_model=List[ProductImageResponse], summary="获取商品图片列表")
async def list_product_images(
    product_id: int,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("product:read")),
    service: ProductImageService = Depends(get_service(ProductImageService)),
):
    """获取商品的所有图片"""
    logger.info(f"开始获取商品图片列表: product_id={product_id}, user_id={current_user.user_id}")
    try:
        return await service.list_product_images(product_id)
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.detail)
    except Exception as e:
        logger.error(f"获取商品图片列表失败: product_id={product_id}, error={str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取商品图片列表失败: {str(e)}")


@router.post("/{product_id}/images", status_code=status.HTTP_201_CREATED, summary="添加商品图片")
async def add_product_image(
    product_id: int,
    image_data: ProductImageCreate,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("product:update")),
    service: ProductImageService = Depends(get_service(ProductImageService)),
):
    """为商品添加图片"""
    logger.info(f"开始添加商品图片: product_id={product_id}, user_id={current_user.user_id}")
    try:
        product_image_id = await service.add_product_image(product_id, image_data)
        logger.info(f"商品图片添加完成: product_id={product_id}, product_image_id={product_image_id}")
        return {"product_image_id": product_image_id, "message": "商品图片添加成功"}
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.detail)
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.detail)
    except Exception as e:
        logger.error(f"添加商品图片失败: product_id={product_id}, error={str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"添加商品图片失败: {str(e)}")


@router.delete("/{product_id}/images/{product_image_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除商品图片")
async def delete_product_image(
    product_id: int,
    product_image_id: int,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("product:update")),
    service: ProductImageService = Depends(get_service(ProductImageService)),
):
    """删除商品图片"""
    logger.info(f"开始删除商品图片: product_id={product_id}, product_image_id={product_image_id}, user_id={current_user.user_id}")
    try:
        await service.delete_product_image(product_id, product_image_id)
        logger.info(f"商品图片删除完成: product_id={product_id}, product_image_id={product_image_id}")
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.detail)
    except Exception as e:
        logger.error(f"删除商品图片失败: product_id={product_id}, product_image_id={product_image_id}, error={str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"删除商品图片失败: {str(e)}")


@router.post("/{product_id}/images/{product_image_id}/primary", summary="设置主图")
async def set_primary_image(
    product_id: int,
    product_image_id: int,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("product:update")),
    service: ProductImageService = Depends(get_service(ProductImageService)),
):
    """设置商品主图"""
    logger.info(f"开始设置主图: product_id={product_id}, product_image_id={product_image_id}, user_id={current_user.user_id}")
    try:
        await service.set_primary_image(product_id, product_image_id)
        logger.info(f"主图设置完成: product_id={product_id}, product_image_id={product_image_id}")
        return {"message": "主图设置成功"}
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.detail)
    except Exception as e:
        logger.error(f"设置主图失败: product_id={product_id}, product_image_id={product_image_id}, error={str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"设置主图失败: {str(e)}")


@router.patch("/{product_id}/images/{product_image_id}/sort", summary="更新图片排序")
async def update_image_sort(
    product_id: int,
    product_image_id: int,
    sort_order: int = Query(..., ge=0, description="排序值"),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("product:update")),
    service: ProductImageService = Depends(get_service(ProductImageService)),
):
    """更新图片排序"""
    logger.info(f"开始更新图片排序: product_id={product_id}, product_image_id={product_image_id}, sort_order={sort_order}, user_id={current_user.user_id}")
    try:
        await service.update_image_sort(product_id, product_image_id, sort_order)
        logger.info(f"图片排序更新完成: product_id={product_id}, product_image_id={product_image_id}, sort_order={sort_order}")
        return {"message": "图片排序更新成功"}
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.detail)
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.detail)
    except Exception as e:
        logger.error(f"更新图片排序失败: product_id={product_id}, product_image_id={product_image_id}, error={str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"更新图片排序失败: {str(e)}")


# ==================== 商品分类关联路由 ====================

@router.get("/{product_id}/categories", response_model=List[ProductCategoryResponse], summary="获取商品分类列表")
async def list_product_categories(
    product_id: int,
    language_id: Optional[int] = Query(None, ge=1, description="语言ID"),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("product:read")),
    service: ProductCategoryService = Depends(get_service(ProductCategoryService)),
):
    """获取商品的所有分类"""
    logger.info(f"开始获取商品分类列表: product_id={product_id}, user_id={current_user.user_id}")
    try:
        return await service.list_product_categories(product_id, language_id)
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.detail)
    except Exception as e:
        logger.error(f"获取商品分类列表失败: product_id={product_id}, error={str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取商品分类列表失败: {str(e)}")


@router.post("/{product_id}/categories", status_code=status.HTTP_201_CREATED, summary="添加商品分类")
async def add_product_category(
    product_id: int,
    category_data: dict = Body(..., description="分类数据，包含category_id"),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("product:update")),
    service: ProductCategoryService = Depends(get_service(ProductCategoryService)),
):
    """为商品添加分类"""
    category_id = category_data.get("category_id")
    if not category_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="category_id是必填字段")
    
    logger.info(f"开始添加商品分类: product_id={product_id}, category_id={category_id}, user_id={current_user.user_id}")
    try:
        await service.add_product_category(product_id, category_id)
        logger.info(f"商品分类添加完成: product_id={product_id}, category_id={category_id}")
        return {"message": "商品分类添加成功"}
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.detail)
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.detail)
    except Exception as e:
        logger.error(f"添加商品分类失败: product_id={product_id}, category_id={category_id}, error={str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"添加商品分类失败: {str(e)}")


@router.delete("/{product_id}/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除商品分类")
async def delete_product_category(
    product_id: int,
    category_id: int,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("product:update")),
    service: ProductCategoryService = Depends(get_service(ProductCategoryService)),
):
    """删除商品分类"""
    logger.info(f"开始删除商品分类: product_id={product_id}, category_id={category_id}, user_id={current_user.user_id}")
    try:
        await service.delete_product_category(product_id, category_id)
        logger.info(f"商品分类删除完成: product_id={product_id}, category_id={category_id}")
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.detail)
    except Exception as e:
        logger.error(f"删除商品分类失败: product_id={product_id}, category_id={category_id}, error={str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"删除商品分类失败: {str(e)}")


@router.patch("/{product_id}/categories", summary="批量更新商品分类")
async def batch_update_product_categories(
    product_id: int,
    category_ids: List[int],
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("product:update")),
    service: ProductCategoryService = Depends(get_service(ProductCategoryService)),
):
    """批量更新商品分类（先删除所有再批量添加）"""
    logger.info(f"开始批量更新商品分类: product_id={product_id}, user_id={current_user.user_id}")
    try:
        await service.batch_update_product_categories(product_id, category_ids)
        logger.info(f"商品分类批量更新完成: product_id={product_id}")
        return {"message": "商品分类批量更新成功"}
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.detail)
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.detail)
    except Exception as e:
        logger.error(f"批量更新商品分类失败: product_id={product_id}, error={str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"批量更新商品分类失败: {str(e)}")

