"""
Product service - 商品服务层
"""
import logging
from typing import List, Optional, Dict, Any, Union
from decimal import Decimal
from datetime import datetime
from tortoise.exceptions import DoesNotExist, IntegrityError

try:
    from app.models.catalog.product import Product
    from app.models.catalog.product_description import ProductDescription
    from app.models.catalog.product_attribute import ProductAttribute
    from app.models.catalog.product_option import ProductOption
    from app.models.catalog.product_option_value import ProductOptionValue
    from app.models.catalog.product_image import ProductImage
    from app.models.catalog.product_to_category import ProductToCategory
    from app.models.catalog.product_related import ProductRelated
    from app.models.catalog.manufacturer import Manufacturer
    from app.models.system.stock_status import StockStatus
    from app.models.localisation.tax_class import TaxClass
    from app.models.localisation.weight_class import WeightClass
    from app.models.localisation.length_class import LengthClass
    from app.models.system.weight_class_description import WeightClassDescription
    from app.models.system.length_class_description import LengthClassDescription
    from app.models.localisation.language import Language
except (ImportError, AttributeError):
    import importlib
    product_module = importlib.import_module('app.models.catalog.product')
    Product = product_module.Product
    product_desc_module = importlib.import_module('app.models.catalog.product_description')
    ProductDescription = product_desc_module.ProductDescription
    # ... 其他导入

from app.schemas.product import (
    ProductCreate, ProductUpdate, ProductResponse, ProductListItem,
    ProductDescriptionCreate, ProductDescriptionResponse,
    ProductAttributeCreate, ProductAttributeResponse,
    ProductOptionCreate, ProductOptionResponse,
    ProductImageCreate, ProductImageResponse,
    ProductCategoryResponse, ProductFilterParams, ProductCopyRequest
)
from app.services.base_service import BaseService
from app.exceptions import NotFoundException, ConflictException, ValidationException

logger = logging.getLogger(__name__)


class ProductService(BaseService):
    """商品服务"""
    
    # ==================== 公共方法：查询 ====================
    
    async def list_products(
        self,
        skip: int = 0,
        limit: int = 20,
        sort: str = "sort_order",
        order: str = "asc",
        filter_params: Optional[ProductFilterParams] = None,
        language_id: Optional[int] = None
    ) -> List[ProductListItem]:
        """
        获取商品列表
        
        Args:
            skip: 跳过的记录数
            limit: 返回的记录数
            sort: 排序字段（sort_order, price, quantity, date_added等）
            order: 排序方向（asc, desc）
            filter_params: 筛选参数
            language_id: 语言ID（用于返回对应语言的名称）
            
        Returns:
            List[ProductListItem]: 商品列表
        """
        logger.info(f"开始获取商品列表: skip={skip}, limit={limit}")
        try:
            query = Product.all()
            
            # 应用筛选条件
            if filter_params:
                # 名称筛选（模糊匹配）
                if filter_params.name:
                    # 使用 values() 方法避免访问不存在的 'id' 字段（ProductDescription 使用复合主键）
                    desc_data_list = await ProductDescription.filter(
                        name__icontains=filter_params.name
                    ).values('product_id')
                    desc_ids = [desc['product_id'] for desc in desc_data_list if desc.get('product_id')]
                    if desc_ids:
                        query = query.filter(product_id__in=desc_ids)
                    else:
                        return []
                
                # 型号筛选（模糊匹配）
                if filter_params.model:
                    query = query.filter(model__icontains=filter_params.model)
                
                # 分类筛选
                if filter_params.category_id:
                    # 通过ProductToCategory关联表筛选
                    ptc_data_list = await ProductToCategory.filter(
                        category_id=filter_params.category_id
                    ).values('product_id')
                    ptc_ids = [ptc['product_id'] for ptc in ptc_data_list if ptc.get('product_id')]
                    if ptc_ids:
                        query = query.filter(product_id__in=ptc_ids)
                    else:
                        return []
                
                # 制造商筛选
                if filter_params.manufacturer_id:
                    query = query.filter(manufacturer_id=filter_params.manufacturer_id)
                
                # 价格范围筛选
                if filter_params.price_from is not None:
                    query = query.filter(price__gte=filter_params.price_from)
                if filter_params.price_to is not None:
                    query = query.filter(price__lte=filter_params.price_to)
                
                # 库存范围筛选
                if filter_params.quantity_from is not None:
                    query = query.filter(quantity__gte=filter_params.quantity_from)
                if filter_params.quantity_to is not None:
                    query = query.filter(quantity__lte=filter_params.quantity_to)
                
                # 状态筛选
                if filter_params.status is not None:
                    query = query.filter(status=filter_params.status)
                
                # 主商品筛选（用于查询变体商品）
                if filter_params.master_id is not None:
                    query = query.filter(master_id=filter_params.master_id)
            
            # 排序
            valid_sort_fields = ["sort_order", "price", "quantity", "date_added", "date_modified", "product_id"]
            sort_field = sort if sort in valid_sort_fields else "sort_order"
            if order == "desc":
                query = query.order_by(f"-{sort_field}")
            else:
                query = query.order_by(sort_field)
            
            products = await query.offset(skip).limit(limit)
            
            # 构建响应
            result = []
            for product in products:
                response = await self._build_product_list_item(product, language_id)
                result.append(response)
            
            logger.info(f"商品列表获取完成: count={len(result)}")
            return result
        except Exception as e:
            logger.error(f"获取商品列表失败: {str(e)}")
            raise
    
    async def get_product(
        self,
        product_id: int,
        language_id: Optional[int] = None,
        include_attributes: bool = False,
        include_options: bool = False,
        include_images: bool = False,
        include_categories: bool = False,
        include_related: bool = False
    ) -> ProductResponse:
        """
        获取商品详情
        
        Args:
            product_id: 商品ID
            language_id: 语言ID（用于返回对应语言的名称）
            include_attributes: 是否包含属性
            include_options: 是否包含选项
            include_images: 是否包含图片
            include_categories: 是否包含分类
            include_related: 是否包含相关商品
            
        Returns:
            ProductResponse: 商品信息
            
        Raises:
            NotFoundException: 商品不存在
        """
        logger.info(f"开始获取商品详情: product_id={product_id}")
        try:
            product = await Product.get_or_none(product_id=product_id)
            if not product:
                raise NotFoundException("商品", product_id)
            
            response = await self._build_product_response(
                product, language_id, include_attributes, include_options,
                include_images, include_categories, include_related
            )
            
            logger.info(f"商品详情获取完成: product_id={product_id}")
            return response
        except NotFoundException:
            raise
        except DoesNotExist:
            raise NotFoundException("商品", product_id)
        except Exception as e:
            logger.error(f"获取商品详情失败: product_id={product_id}, error={str(e)}")
            raise
    
    # ==================== 公共方法：创建 ====================
    
    async def create_product(self, data: ProductCreate) -> ProductResponse:
        """
        创建商品
        
        Args:
            data: 商品创建数据
            
        Returns:
            ProductResponse: 创建的商品信息
            
        Raises:
            ValidationException: 数据验证失败
            ConflictException: 数据冲突（如SKU重复）
        """
        logger.info(f"开始创建商品: model={data.model}")
        try:
            # 常规校验
            await self._validate_product_data(data)
            
            # 创建商品主记录
            product_data = data.model_dump(exclude={'descriptions', 'attributes', 'options', 'images', 'category_ids', 'related_product_ids'})
            product = await Product.create(**product_data)
            
            # 创建多语言描述
            if data.descriptions:
                await self._create_product_descriptions(product.product_id, data.descriptions)
            
            # 创建商品属性
            if data.attributes:
                await self._create_product_attributes(product.product_id, data.attributes)
            
            # 创建商品选项
            if data.options:
                await self._create_product_options(product.product_id, data.options)
            
            # 创建商品图片
            if data.images:
                await self._create_product_images(product.product_id, data.images)
            
            # 创建商品分类关联
            if data.category_ids:
                await self._create_product_categories(product.product_id, data.category_ids)
            
            # 创建相关商品关联
            if data.related_product_ids:
                await self._create_product_related(product.product_id, data.related_product_ids)
            
            logger.info(f"商品创建完成: product_id={product.product_id}")
            
            # 返回创建的商品
            return await self.get_product(product.product_id)
        except (ValidationException, ConflictException):
            raise
        except IntegrityError as e:
            logger.error(f"创建商品失败: model={data.model}, error={str(e)}")
            if "sku" in str(e).lower() or "duplicate" in str(e).lower():
                raise ConflictException("SKU已存在", {"sku": data.sku})
            raise ValidationException("创建商品失败", {"error": str(e)})
        except Exception as e:
            logger.error(f"创建商品失败: model={data.model}, error={str(e)}")
            raise
    
    # ==================== 公共方法：更新 ====================
    
    async def update_product(self, product_id: int, data: ProductUpdate) -> ProductResponse:
        """
        完整更新商品
        
        Args:
            product_id: 商品ID
            data: 商品更新数据
            
        Returns:
            ProductResponse: 更新后的商品信息
            
        Raises:
            NotFoundException: 商品不存在
            ValidationException: 数据验证失败
        """
        logger.info(f"开始更新商品: product_id={product_id}")
        try:
            product = await Product.get_or_none(product_id=product_id)
            if not product:
                raise NotFoundException("商品", product_id)
            
            # 常规校验
            await self._validate_product_data(data, product_id=product_id)
            
            # 更新商品主记录
            update_data = data.model_dump(exclude_unset=True, exclude={'descriptions', 'attributes', 'options', 'images', 'category_ids', 'related_product_ids'})
            if update_data:
                update_data['date_modified'] = datetime.now()
                await Product.filter(product_id=product_id).update(**update_data)
            
            # 更新多语言描述
            if data.descriptions is not None:
                await self._update_product_descriptions(product_id, data.descriptions)
            
            # 更新商品属性
            if data.attributes is not None:
                await self._update_product_attributes(product_id, data.attributes)
            
            # 更新商品选项
            if data.options is not None:
                await self._update_product_options(product_id, data.options)
            
            # 更新商品图片
            if data.images is not None:
                await self._update_product_images(product_id, data.images)
            
            # 更新商品分类关联
            if data.category_ids is not None:
                await self._update_product_categories(product_id, data.category_ids)
            
            # 更新相关商品关联
            if data.related_product_ids is not None:
                await self._update_product_related(product_id, data.related_product_ids)
            
            logger.info(f"商品更新完成: product_id={product_id}")
            
            # 返回更新后的商品
            return await self.get_product(product_id)
        except NotFoundException:
            raise
        except (ValidationException, ConflictException):
            raise
        except Exception as e:
            logger.error(f"更新商品失败: product_id={product_id}, error={str(e)}")
            raise
    
    async def patch_product(self, product_id: int, data: Dict[str, Any]) -> ProductResponse:
        """
        部分更新商品
        
        Args:
            product_id: 商品ID
            data: 部分更新数据（字典格式）
            
        Returns:
            ProductResponse: 更新后的商品信息
            
        Raises:
            NotFoundException: 商品不存在
            ValidationException: 数据验证失败
        """
        logger.info(f"开始部分更新商品: product_id={product_id}")
        try:
            product = await Product.get_or_none(product_id=product_id)
            if not product:
                raise NotFoundException("商品", product_id)
            
            # 将字典转换为ProductUpdate对象（只包含提供的字段）
            update_data = ProductUpdate(**data)
            
            # 调用完整更新方法
            return await self.update_product(product_id, update_data)
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"部分更新商品失败: product_id={product_id}, error={str(e)}")
            raise
    
    # ==================== 公共方法：删除 ====================
    
    async def delete_product(self, product_id: int) -> None:
        """
        删除商品
        
        Args:
            product_id: 商品ID
            
        Raises:
            NotFoundException: 商品不存在
            ConflictException: 存在关联数据，无法删除
        """
        logger.info(f"开始删除商品: product_id={product_id}")
        try:
            product = await Product.get_or_none(product_id=product_id)
            if not product:
                raise NotFoundException("商品", product_id)
            
            # 检查商品依赖关系
            dependencies = await self._check_product_dependencies(product_id)
            
            # 检查是否有关联订单（参照PHP实现：虽然PHP没有检查，但实际业务中应该检查）
            if dependencies["has_orders"]:
                raise ConflictException(
                    "无法删除商品",
                    {"message": f"该商品存在 {dependencies['order_count']} 个关联订单，无法删除"}
                )
            
            # 检查是否在购物车中（参照PHP实现：虽然PHP没有检查，但实际业务中应该检查）
            if dependencies.get("has_cart", False):
                raise ConflictException(
                    "无法删除商品",
                    {"message": f"该商品在购物车中存在 {dependencies.get('cart_count', 0)} 次，无法删除"}
                )
            
            # 删除关联数据（参照PHP实现：先删除关联数据，再删除主记录）
            await ProductDescription.filter(product_id=product_id).delete()
            await ProductAttribute.filter(product_id=product_id).delete()
            await ProductOption.filter(product_id=product_id).delete()
            await ProductImage.filter(product_id=product_id).delete()
            await ProductToCategory.filter(product_id=product_id).delete()
            await ProductRelated.filter(product_id=product_id).delete()
            await ProductRelated.filter(related_id=product_id).delete()  # 删除作为相关商品的关联
            
            # 处理变体商品（参照PHP实现：editMasterId($product_id, 0)）
            # 如果删除的是主商品，将变体商品的master_id更新为0
            if dependencies["has_variants"]:
                await Product.filter(master_id=product_id).update(master_id=0)
            
            # 删除商品主记录（参照PHP实现：先删除主记录，但Python先删除关联数据更安全）
            await Product.filter(product_id=product_id).delete()
            
            logger.info(f"商品删除完成: product_id={product_id}")
        except NotFoundException:
            raise
        except ConflictException:
            raise
        except Exception as e:
            logger.error(f"删除商品失败: product_id={product_id}, error={str(e)}")
            raise
    
    # ==================== 公共方法：复制 ====================
    
    async def copy_product(self, product_id: int, copy_request: ProductCopyRequest) -> ProductResponse:
        """
        复制商品
        
        Args:
            product_id: 源商品ID
            copy_request: 复制请求参数
            
        Returns:
            ProductResponse: 复制后的商品信息
            
        Raises:
            NotFoundException: 源商品不存在
        """
        logger.info(f"开始复制商品: product_id={product_id}")
        try:
            source_product = await Product.get_or_none(product_id=product_id)
            if not source_product:
                raise NotFoundException("商品", product_id)
            
            # 获取源商品的所有数据
            source_data = await self.get_product(
                product_id,
                include_attributes=True,
                include_options=True,
                include_images=True,
                include_categories=True,
                include_related=True
            )
            
            # 构建新商品数据
            product_dict = source_data.model_dump(exclude={'product_id', 'date_added', 'date_modified'})
            
            # 清空唯一字段（参照PHP实现：清空sku, upc, rating, status）
            # 注意：model也是唯一字段，需要修改以避免冲突（不能设为None，因为ProductCreate要求model是字符串）
            product_dict['sku'] = None
            product_dict['upc'] = None
            product_dict['rating'] = 0
            product_dict['status'] = 0
            # 修改model，添加时间戳后缀以避免冲突
            import time
            if product_dict.get('model'):
                product_dict['model'] = f"{product_dict['model']}_copy_{int(time.time())}"
            
            # 处理名称后缀
            if copy_request.name_suffix:
                # 更新所有语言的名称
                if 'descriptions' in product_dict and product_dict['descriptions']:
                    for desc in product_dict['descriptions']:
                        if 'name' in desc:
                            desc['name'] = f"{desc['name']} {copy_request.name_suffix}"
            
            # 根据复制选项决定是否包含关联数据
            if not copy_request.copy_attributes:
                product_dict.pop('attributes', None)
            if not copy_request.copy_options:
                product_dict.pop('options', None)
            if not copy_request.copy_images:
                product_dict.pop('images', None)
            if not copy_request.copy_categories:
                product_dict.pop('categories', None)
                product_dict.pop('category_ids', None)
            
            # 处理相关商品（始终复制）
            if 'related_products' in product_dict:
                related_ids = [r.get('product_id') for r in product_dict['related_products'] if r.get('product_id')]
                product_dict['related_product_ids'] = related_ids
                product_dict.pop('related_products', None)
            
            # 处理分类ID
            if 'categories' in product_dict and product_dict['categories']:
                category_ids = [c.get('category_id') for c in product_dict['categories'] if c.get('category_id')]
                product_dict['category_ids'] = category_ids
                product_dict.pop('categories', None)
            
            # 创建新商品
            create_data = ProductCreate(**product_dict)
            new_product = await self.create_product(create_data)
            
            logger.info(f"商品复制完成: source_id={product_id}, new_id={new_product.product_id}")
            return new_product
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"复制商品失败: product_id={product_id}, error={str(e)}")
            raise
    
    # ==================== 私有方法：数据验证 ====================
    
    async def _validate_product_data(self, data: Union[ProductCreate, ProductUpdate], product_id: Optional[int] = None):
        """
        验证商品数据
        
        Args:
            data: 商品数据
            product_id: 商品ID（更新时使用）
            
        Raises:
            ValidationException: 数据验证失败
        """
        # ==================== 常规校验 ====================
        
        # 验证必需字段（商品型号）
        if isinstance(data, ProductCreate):
            # 允许model为None（复制商品时可能清空model）
            if data.model is None:
                raise ValidationException("商品型号不能为空", {"model": "商品型号是必填字段"})
            if len(data.model.strip()) == 0:
                raise ValidationException("商品型号不能为空", {"model": "商品型号不能为空字符串"})
            if len(data.model) > 64:
                raise ValidationException("商品型号长度不能超过64个字符", {"model": f"当前长度: {len(data.model)}"})
        elif isinstance(data, ProductUpdate) and data.model is not None:
            if len(data.model.strip()) == 0:
                raise ValidationException("商品型号不能为空", {"model": "商品型号不能为空字符串"})
            if len(data.model) > 64:
                raise ValidationException("商品型号长度不能超过64个字符", {"model": f"当前长度: {len(data.model)}"})
        
        # 验证商品型号唯一性
        if isinstance(data, ProductCreate) or (isinstance(data, ProductUpdate) and data.model is not None):
            model_to_check = data.model if isinstance(data, ProductCreate) else data.model
            if model_to_check:
                existing = await Product.filter(model=model_to_check).first()
                if existing and (not product_id or existing.product_id != product_id):
                    raise ConflictException("商品型号已存在", {"model": model_to_check})
        
        # 验证价格范围（>= 0）
        if isinstance(data, ProductCreate):
            if data.price < 0:
                raise ValidationException("商品价格不能小于0", {"price": f"当前价格: {data.price}"})
        elif isinstance(data, ProductUpdate) and data.price is not None:
            if data.price < 0:
                raise ValidationException("商品价格不能小于0", {"price": f"当前价格: {data.price}"})
        
        # 验证库存数量（>= 0）
        if isinstance(data, ProductCreate):
            if data.quantity < 0:
                raise ValidationException("库存数量不能小于0", {"quantity": f"当前数量: {data.quantity}"})
        elif isinstance(data, ProductUpdate) and data.quantity is not None:
            if data.quantity < 0:
                raise ValidationException("库存数量不能小于0", {"quantity": f"当前数量: {data.quantity}"})
        
        # 验证多语言描述（至少一个语言）
        if isinstance(data, ProductCreate):
            if not data.descriptions or len(data.descriptions) == 0:
                raise ValidationException("商品描述不能为空", {"descriptions": "至少需要提供一个语言的商品描述"})
            
            # 验证语言ID是否重复
            language_ids = [desc.language_id for desc in data.descriptions]
            if len(language_ids) != len(set(language_ids)):
                raise ValidationException("描述中的语言ID不能重复", {"descriptions": "每个语言只能有一个描述"})
            
            # 验证每个描述的名称长度和内容
            for desc in data.descriptions:
                # 验证语言是否存在
                language = await Language.filter(language_id=desc.language_id).first()
                if not language:
                    raise ValidationException(f"语言ID {desc.language_id} 不存在", {"language_id": desc.language_id})
                
                # 验证名称长度（1-255字符）
                if not desc.name or len(desc.name.strip()) == 0:
                    raise ValidationException(f"语言ID {desc.language_id} 的商品名称不能为空", {"language_id": desc.language_id})
                if len(desc.name) > 255:
                    raise ValidationException(
                        f"语言ID {desc.language_id} 的商品名称长度不能超过255个字符",
                        {"language_id": desc.language_id, "name_length": len(desc.name)}
                    )
        
        elif isinstance(data, ProductUpdate) and data.descriptions is not None:
            if len(data.descriptions) == 0:
                raise ValidationException("商品描述不能为空", {"descriptions": "至少需要提供一个语言的商品描述"})
            
            # 验证语言ID是否重复
            language_ids = [desc.language_id for desc in data.descriptions]
            if len(language_ids) != len(set(language_ids)):
                raise ValidationException("描述中的语言ID不能重复", {"descriptions": "每个语言只能有一个描述"})
            
            # 验证每个描述的名称长度和内容
            for desc in data.descriptions:
                # 验证语言是否存在
                language = await Language.filter(language_id=desc.language_id).first()
                if not language:
                    raise ValidationException(f"语言ID {desc.language_id} 不存在", {"language_id": desc.language_id})
                
                # 验证名称长度（1-255字符）
                if not desc.name or len(desc.name.strip()) == 0:
                    raise ValidationException(f"语言ID {desc.language_id} 的商品名称不能为空", {"language_id": desc.language_id})
                if len(desc.name) > 255:
                    raise ValidationException(
                        f"语言ID {desc.language_id} 的商品名称长度不能超过255个字符",
                        {"language_id": desc.language_id, "name_length": len(desc.name)}
                    )
        
        # 验证SKU唯一性（如果提供）
        if data.sku:
            if len(data.sku) > 64:
                raise ValidationException("SKU长度不能超过64个字符", {"sku": f"当前长度: {len(data.sku)}"})
            existing = await Product.filter(sku=data.sku).first()
            if existing and (not product_id or existing.product_id != product_id):
                raise ConflictException("SKU已存在", {"sku": data.sku})
        
        # ==================== 逻辑校验 ====================
        
        # 验证主商品存在性（如果是变体商品，参照PHP实现：需要验证主商品存在且不是变体商品）
        if data.master_id and data.master_id > 0:
            master = await Product.get_or_none(product_id=data.master_id)
            if not master:
                raise ValidationException("主商品不存在", {"master_id": f"主商品ID {data.master_id} 不存在"})
            # 验证主商品本身不是变体商品（主商品的master_id应该为0）
            if master.master_id and master.master_id > 0:
                raise ValidationException("主商品不能是变体商品", {"master_id": f"商品ID {data.master_id} 本身是变体商品，不能作为主商品"})
        
        # 验证制造商存在性
        if data.manufacturer_id and data.manufacturer_id > 0:
            manufacturer = await Manufacturer.get_or_none(manufacturer_id=data.manufacturer_id)
            if not manufacturer:
                raise ValidationException("制造商不存在", {"manufacturer_id": f"制造商ID {data.manufacturer_id} 不存在"})
        
        # 验证库存状态存在性
        # 注意：StockStatus使用复合主键，需要使用values()避免访问不存在的id字段
        if data.stock_status_id and data.stock_status_id > 0:
            stock_status_data_list = await StockStatus.filter(stock_status_id=data.stock_status_id).values('stock_status_id')
            if not stock_status_data_list:
                raise ValidationException("库存状态不存在", {"stock_status_id": f"库存状态ID {data.stock_status_id} 不存在"})
        
        # 验证税类存在性
        if data.tax_class_id and data.tax_class_id > 0:
            tax_class = await TaxClass.get_or_none(tax_class_id=data.tax_class_id)
            if not tax_class:
                raise ValidationException("税类不存在", {"tax_class_id": f"税类ID {data.tax_class_id} 不存在"})
        
        # 验证重量单位存在性
        if data.weight_class_id and data.weight_class_id > 0:
            weight_class = await WeightClass.get_or_none(weight_class_id=data.weight_class_id)
            if not weight_class:
                raise ValidationException("重量单位不存在", {"weight_class_id": f"重量单位ID {data.weight_class_id} 不存在"})
        
        # 验证长度单位存在性
        if data.length_class_id and data.length_class_id > 0:
            length_class = await LengthClass.get_or_none(length_class_id=data.length_class_id)
            if not length_class:
                raise ValidationException("长度单位不存在", {"length_class_id": f"长度单位ID {data.length_class_id} 不存在"})
        
        # 验证分类存在性（参照PHP实现：需要验证分类是否存在）
        if hasattr(data, 'category_ids') and data.category_ids:
            from app.models.catalog.category import Category
            for category_id in data.category_ids:
                category = await Category.get_or_none(category_id=category_id)
                if not category:
                    raise ValidationException("分类不存在", {"category_ids": f"分类ID {category_id} 不存在"})
        
        # 验证相关商品存在性
        if hasattr(data, 'related_product_ids') and data.related_product_ids:
            for related_id in data.related_product_ids:
                if related_id == product_id:
                    raise ValidationException("商品不能关联自己", {"related_product_ids": "相关商品ID不能与当前商品ID相同"})
                related = await Product.get_or_none(product_id=related_id)
                if not related:
                    raise ValidationException("相关商品不存在", {"related_product_ids": f"相关商品ID {related_id} 不存在"})
    
    # ==================== 私有方法：辅助方法 ====================
    
    async def _get_product_name(self, product_id: int, language_id: Optional[int] = None) -> Optional[str]:
        """
        获取商品名称（多语言）
        
        Args:
            product_id: 商品ID
            language_id: 语言ID
            
        Returns:
            Optional[str]: 商品名称，如果不存在则返回None
        """
        try:
            if language_id:
                # 使用 values() 方法避免访问不存在的 'id' 字段（ProductDescription 使用复合主键）
                desc_data_list = await ProductDescription.filter(
                    product_id=product_id,
                    language_id=language_id
                ).limit(1).values('name')
                if desc_data_list:
                    return desc_data_list[0].get('name')
            
            # 如果没有指定语言，返回第一个描述
            desc_data_list = await ProductDescription.filter(
                product_id=product_id
            ).limit(1).values('name')
            return desc_data_list[0]['name'] if desc_data_list else None
        except Exception:
            return None
    
    async def _check_product_dependencies(self, product_id: int) -> Dict[str, Any]:
        """
        检查商品依赖关系
        
        Args:
            product_id: 商品ID
            
        Returns:
            Dict[str, Any]: 依赖关系信息，包含：
                - has_variants: 是否有变体商品
                - variant_count: 变体商品数量
                - has_orders: 是否有关联订单
                - order_count: 关联订单数量
                - has_cart: 是否在购物车中
                - cart_count: 购物车中的数量
                - has_related: 是否作为其他商品的相关商品
                - related_count: 作为相关商品的数量
        """
        dependencies = {
            "has_variants": False,
            "variant_count": 0,
            "has_orders": False,
            "order_count": 0,
            "has_cart": False,
            "cart_count": 0,
            "has_related": False,
            "related_count": 0
        }
        
        try:
            # 检查是否有变体商品
            variants = await Product.filter(master_id=product_id).all()
            if variants:
                dependencies["has_variants"] = True
                dependencies["variant_count"] = len(variants)
            
            # 检查是否有关联订单（参照PHP实现：删除商品前需要检查订单关联）
            # 注意：PHP实现中删除商品时没有检查订单，直接删除，但实际业务中应该检查
            try:
                from app.models.order.order_product import OrderProduct
                order_count = await OrderProduct.filter(product_id=product_id).count()
                if order_count > 0:
                    dependencies["has_orders"] = True
                    dependencies["order_count"] = order_count
            except ImportError:
                # 如果订单模型未导入，跳过检查
                pass
            
            # 检查是否在购物车中（参照PHP实现：购物车数据存储在oc_cart表）
            # 注意：PHP实现中删除商品时没有检查购物车，但实际业务中应该检查
            try:
                from app.models.order.cart import Cart
                cart_count = await Cart.filter(product_id=product_id).count()
                if cart_count > 0:
                    dependencies["has_cart"] = True
                    dependencies["cart_count"] = cart_count
            except ImportError:
                # 如果购物车模型未导入，跳过检查
                pass
            
            # 检查是否作为其他商品的相关商品
            # 注意：ProductRelated使用复合主键，需要使用values()避免访问不存在的id字段
            related_as_related_data = await ProductRelated.filter(related_id=product_id).values('product_id', 'related_id')
            if related_as_related_data:
                dependencies["has_related"] = True
                dependencies["related_count"] = len(related_as_related_data)
            
            return dependencies
        except Exception as e:
            logger.warning(f"检查商品依赖关系失败: product_id={product_id}, error={str(e)}")
            return dependencies
    
    # ==================== 私有方法：构建响应 ====================
    
    async def _build_product_list_item(self, product: Product, language_id: Optional[int] = None) -> ProductListItem:
        """
        构建商品列表项响应
        
        Args:
            product: 商品模型
            language_id: 语言ID
            
        Returns:
            ProductListItem: 商品列表项
        """
        # 获取商品名称
        name = await self._get_product_name(product.product_id, language_id)
        
        # 获取制造商信息
        manufacturer = None
        if product.manufacturer_id:
            mfr = await Manufacturer.get_or_none(manufacturer_id=product.manufacturer_id)
            if mfr:
                manufacturer = {
                    "manufacturer_id": mfr.manufacturer_id,
                    "name": mfr.name
                }
        
        # 获取分类信息
        categories = []
        ptc_data_list = await ProductToCategory.filter(product_id=product.product_id).values('category_id')
        if ptc_data_list:
            # TODO: 获取分类名称
            categories = [{"category_id": ptc['category_id']} for ptc in ptc_data_list]
        
        return ProductListItem(
            product_id=product.product_id,
            master_id=product.master_id or 0,
            model=product.model or "",
            sku=product.sku,
            name=name,
            price=str(product.price) if product.price else "0.0000",
            quantity=product.quantity or 0,
            status=product.status or 0,
            image=product.image,
            manufacturer=manufacturer,
            categories=categories,
            date_added=product.date_added,
            date_modified=product.date_modified
        )
    
    async def _build_product_response(
        self,
        product: Product,
        language_id: Optional[int] = None,
        include_attributes: bool = False,
        include_options: bool = False,
        include_images: bool = False,
        include_categories: bool = False,
        include_related: bool = False
    ) -> ProductResponse:
        """
        构建商品响应
        
        Args:
            product: 商品模型
            language_id: 语言ID
            include_attributes: 是否包含属性
            include_options: 是否包含选项
            include_images: 是否包含图片
            include_categories: 是否包含分类
            include_related: 是否包含相关商品
            
        Returns:
            ProductResponse: 商品响应
        """
        # 获取多语言描述
        descriptions_data = await ProductDescription.filter(
            product_id=product.product_id
        ).values('product_id', 'language_id', 'name', 'description', 'tag', 'meta_title', 'meta_description', 'meta_keyword')
        
        descriptions = []
        name = None
        for desc_data in descriptions_data:
            # 获取语言代码
            language_code = None
            if desc_data.get('language_id'):
                lang = await Language.get_or_none(language_id=desc_data['language_id'])
                if lang:
                    language_code = lang.code
            
            desc_response = ProductDescriptionResponse(
                language_id=desc_data['language_id'],
                language_code=language_code,
                name=desc_data.get('name'),
                description=desc_data.get('description'),
                tag=desc_data.get('tag'),
                meta_title=desc_data.get('meta_title'),
                meta_description=desc_data.get('meta_description'),
                meta_keyword=desc_data.get('meta_keyword')
            )
            descriptions.append(desc_response)
            
            # 设置当前语言的名称
            if language_id and desc_data['language_id'] == language_id:
                name = desc_data.get('name')
        
        # 获取关联信息
        manufacturer = None
        if product.manufacturer_id:
            mfr = await Manufacturer.get_or_none(manufacturer_id=product.manufacturer_id)
            if mfr:
                manufacturer = {
                    "manufacturer_id": mfr.manufacturer_id,
                    "name": mfr.name
                }
        
        stock_status = None
        if product.stock_status_id and language_id:
            status_data = await StockStatus.filter(
                stock_status_id=product.stock_status_id,
                language_id=language_id
            ).values('name')
            if status_data:
                stock_status = {
                    "stock_status_id": product.stock_status_id,
                    "name": status_data[0].get('name')
                }
        
        tax_class = None
        if product.tax_class_id:
            tc = await TaxClass.get_or_none(tax_class_id=product.tax_class_id)
            if tc:
                tax_class = {
                    "tax_class_id": tc.tax_class_id,
                    "title": tc.title
                }
        
        weight_class = None
        if product.weight_class_id and language_id:
            wc_desc_data = await WeightClassDescription.filter(
                weight_class_id=product.weight_class_id,
                language_id=language_id
            ).values('title', 'unit')
            if wc_desc_data:
                weight_class = {
                    "weight_class_id": product.weight_class_id,
                    "title": wc_desc_data[0].get('title'),
                    "unit": wc_desc_data[0].get('unit')
                }
        
        length_class = None
        if product.length_class_id and language_id:
            lc_desc_data = await LengthClassDescription.filter(
                length_class_id=product.length_class_id,
                language_id=language_id
            ).values('title', 'unit')
            if lc_desc_data:
                length_class = {
                    "length_class_id": product.length_class_id,
                    "title": lc_desc_data[0].get('title'),
                    "unit": lc_desc_data[0].get('unit')
                }
        
        # 构建响应
        response_dict = {
            "product_id": product.product_id,
            "master_id": product.master_id or 0,
            "model": product.model or "",
            "sku": product.sku,
            "upc": product.upc,
            "ean": product.ean,
            "jan": product.jan,
            "isbn": product.isbn,
            "mpn": product.mpn,
            "location": product.location,
            "quantity": product.quantity or 0,
            "minimum": product.minimum or 1,
            "subtract": product.subtract or 1,
            "stock_status_id": product.stock_status_id or 0,
            "image": product.image,
            "manufacturer_id": product.manufacturer_id or 0,
            "shipping": product.shipping or 1,
            "price": product.price or Decimal('0.0000'),
            "points": product.points or 0,
            "tax_class_id": product.tax_class_id or 0,
            "date_available": product.date_available,
            "weight": product.weight or Decimal('0.00000000'),
            "weight_class_id": product.weight_class_id or 0,
            "length": product.length or Decimal('0.00000000'),
            "width": product.width or Decimal('0.00000000'),
            "height": product.height or Decimal('0.00000000'),
            "length_class_id": product.length_class_id or 0,
            "status": product.status or 0,
            "sort_order": product.sort_order or 0,
            "descriptions": descriptions,
            "name": name,
            "manufacturer": manufacturer,
            "stock_status": stock_status,
            "tax_class": tax_class,
            "weight_class": weight_class,
            "length_class": length_class,
            "date_added": product.date_added,
            "date_modified": product.date_modified
        }
        
        # 根据include参数添加关联数据
        if include_attributes:
            response_dict["attributes"] = await self._get_product_attributes(product.product_id, language_id)
        
        if include_options:
            response_dict["options"] = await self._get_product_options(product.product_id, language_id)
        
        if include_images:
            response_dict["images"] = await self._get_product_images(product.product_id)
        
        if include_categories:
            response_dict["categories"] = await self._get_product_categories(product.product_id, language_id)
        
        if include_related:
            response_dict["related_products"] = await self._get_product_related(product.product_id, language_id)
        
        return ProductResponse(**response_dict)
    
    # ==================== 私有方法：关联数据操作 ====================
    # 这些方法将在后续实现中补充
    
    async def _create_product_descriptions(self, product_id: int, descriptions: List[ProductDescriptionCreate]):
        """创建商品描述"""
        for desc in descriptions:
            await ProductDescription.create(
                product_id=product_id,
                language_id=desc.language_id,
                name=desc.name,
                description=desc.description,
                tag=desc.tag,
                meta_title=desc.meta_title,
                meta_description=desc.meta_description,
                meta_keyword=desc.meta_keyword
            )
    
    async def _update_product_descriptions(self, product_id: int, descriptions: List[ProductDescriptionCreate]):
        """更新商品描述"""
        # 删除现有描述
        await ProductDescription.filter(product_id=product_id).delete()
        # 创建新描述
        await self._create_product_descriptions(product_id, descriptions)
    
    async def _create_product_attributes(self, product_id: int, attributes: List[ProductAttributeCreate]):
        """创建商品属性"""
        from app.services.product_attribute_service import ProductAttributeService
        service = ProductAttributeService()
        
        for attr in attributes:
            # 为每个语言的描述创建属性记录
            for desc in attr.descriptions:
                await service.add_product_attribute(
                    product_id=product_id,
                    attribute_id=attr.attribute_id,
                    language_id=desc.language_id,
                    text=desc.text
                )
    
    async def _update_product_attributes(self, product_id: int, attributes: List[ProductAttributeCreate]):
        """更新商品属性"""
        # 删除现有属性
        from app.models.catalog.product_attribute import ProductAttribute
        await ProductAttribute.filter(product_id=product_id).delete()
        # 创建新属性
        await self._create_product_attributes(product_id, attributes)
    
    async def _create_product_options(self, product_id: int, options: List[ProductOptionCreate]):
        """创建商品选项"""
        from app.services.product_option_service import ProductOptionService
        service = ProductOptionService()
        
        for option in options:
            # 添加商品选项
            product_option_id = await service.add_product_option(
                product_id=product_id,
                option_data=option
            )
    
    async def _update_product_options(self, product_id: int, options: List[ProductOptionCreate]):
        """更新商品选项"""
        # 删除现有选项（包括选项值）
        from app.models.catalog.product_option import ProductOption
        from app.models.catalog.product_option_value import ProductOptionValue
        
        # 获取所有product_option_id
        product_options = await ProductOption.filter(product_id=product_id).all()
        product_option_ids = [po.product_option_id for po in product_options if po.product_option_id]
        
        # 删除选项值
        if product_option_ids:
            await ProductOptionValue.filter(product_option_id__in=product_option_ids).delete()
        
        # 删除选项
        await ProductOption.filter(product_id=product_id).delete()
        
        # 创建新选项
        await self._create_product_options(product_id, options)
    
    async def _create_product_images(self, product_id: int, images: List[ProductImageCreate]):
        """创建商品图片"""
        for img in images:
            await ProductImage.create(
                product_id=product_id,
                image=img.image,
                sort_order=img.sort_order
            )
    
    async def _update_product_images(self, product_id: int, images: List[ProductImageCreate]):
        """更新商品图片"""
        # 删除现有图片
        await ProductImage.filter(product_id=product_id).delete()
        # 创建新图片
        await self._create_product_images(product_id, images)
    
    async def _create_product_categories(self, product_id: int, category_ids: List[int]):
        """创建商品分类关联"""
        # 注意：ProductToCategory使用复合主键，需要使用values()查询
        for category_id in category_ids:
            # 检查是否已存在（复合主键表需要使用values()查询）
            existing_data_list = await ProductToCategory.filter(
                product_id=product_id,
                category_id=category_id
            ).values('product_id', 'category_id')
            
            if not existing_data_list:
                # 不存在则创建
                await ProductToCategory.create(
                    product_id=product_id,
                    category_id=category_id
                )
    
    async def _update_product_categories(self, product_id: int, category_ids: List[int]):
        """更新商品分类关联"""
        # 删除现有关联
        await ProductToCategory.filter(product_id=product_id).delete()
        # 创建新关联
        await self._create_product_categories(product_id, category_ids)
    
    async def _create_product_related(self, product_id: int, related_ids: List[int]):
        """创建相关商品关联"""
        # 注意：ProductRelated使用复合主键，需要使用values()查询
        for related_id in related_ids:
            # 检查是否已存在（复合主键表需要使用values()查询）
            existing_data_list = await ProductRelated.filter(
                product_id=product_id,
                related_id=related_id
            ).values('product_id', 'related_id')
            
            if not existing_data_list:
                # 不存在则创建
                await ProductRelated.create(
                    product_id=product_id,
                    related_id=related_id
                )
    
    async def _update_product_related(self, product_id: int, related_ids: List[int]):
        """更新相关商品关联"""
        # 删除现有关联
        await ProductRelated.filter(product_id=product_id).delete()
        # 创建新关联
        await self._create_product_related(product_id, related_ids)
    
    async def _get_product_attributes(self, product_id: int, language_id: Optional[int] = None) -> List[ProductAttributeResponse]:
        """获取商品属性"""
        from app.services.product_attribute_service import ProductAttributeService
        service = ProductAttributeService()
        return await service.list_product_attributes(product_id, language_id)
    
    async def _get_product_options(self, product_id: int, language_id: Optional[int] = None) -> List[ProductOptionResponse]:
        """获取商品选项"""
        from app.services.product_option_service import ProductOptionService
        service = ProductOptionService()
        return await service.list_product_options(product_id, language_id)
    
    async def _get_product_images(self, product_id: int) -> List[ProductImageResponse]:
        """获取商品图片"""
        images = await ProductImage.filter(product_id=product_id).order_by('sort_order').all()
        return [
            ProductImageResponse(
                product_image_id=img.product_image_id,
                image=img.image or "",
                sort_order=img.sort_order or 0
            )
            for img in images
        ]
    
    async def _get_product_categories(self, product_id: int, language_id: Optional[int] = None) -> List[ProductCategoryResponse]:
        """获取商品分类"""
        from app.services.product_category_service import ProductCategoryService
        service = ProductCategoryService()
        return await service.list_product_categories(product_id, language_id)
    
    async def _get_product_related(self, product_id: int, language_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取相关商品"""
        # 注意：ProductRelated使用复合主键，需要使用values()避免访问不存在的id字段
        related_data_list = await ProductRelated.filter(
            product_id=product_id
        ).values('product_id', 'related_id')
        
        related_ids = [rel['related_id'] for rel in related_data_list if rel.get('related_id')]
        
        if not related_ids:
            return []
        
        # 获取相关商品信息
        related_products = await Product.filter(product_id__in=related_ids).all()
        product_map = {p.product_id: p for p in related_products}
        
        result = []
        for related_id in related_ids:
            product = product_map.get(related_id)
            if product:
                # 获取商品名称
                name = await self._get_product_name(related_id, language_id)
                result.append({
                    "product_id": related_id,
                    "name": name,
                    "model": product.model or "",
                    "price": str(product.price) if product.price else "0.0000"
                })
        
        return result

