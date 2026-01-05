"""
Manufacturer service - 制造商服务层
"""
import logging
from typing import List, Optional, Dict
from tortoise.exceptions import DoesNotExist, IntegrityError

try:
    from app.models.catalog.manufacturer import Manufacturer
    from app.models.catalog.manufacturer_to_store import ManufacturerToStore
    from app.models.catalog.manufacturer_to_layout import ManufacturerToLayout
    from app.models.catalog.product import Product
    from app.models.system.store import Store
    from app.models.design.layout import Layout
    from app.models.system.seo_url import SeoUrl
except (ImportError, AttributeError):
    import importlib
    manufacturer_module = importlib.import_module('app.models.catalog.manufacturer')
    Manufacturer = manufacturer_module.Manufacturer
    manufacturer_to_store_module = importlib.import_module('app.models.catalog.manufacturer_to_store')
    ManufacturerToStore = manufacturer_to_store_module.ManufacturerToStore
    manufacturer_to_layout_module = importlib.import_module('app.models.catalog.manufacturer_to_layout')
    ManufacturerToLayout = manufacturer_to_layout_module.ManufacturerToLayout
    product_module = importlib.import_module('app.models.catalog.product')
    Product = product_module.Product
    store_module = importlib.import_module('app.models.system.store')
    Store = store_module.Store
    layout_module = importlib.import_module('app.models.design.layout')
    Layout = layout_module.Layout
    seo_url_module = importlib.import_module('app.models.system.seo_url')
    SeoUrl = seo_url_module.SeoUrl

from app.schemas.manufacturer import (
    ManufacturerCreate, ManufacturerUpdate, ManufacturerPatch, ManufacturerResponse,
    ManufacturerListItem, ManufacturerAutocompleteItem, ManufacturerBatchDeleteRequest,
    ManufacturerBatchDeleteResponse, ManufacturerStoreUpdateRequest, ManufacturerStoreUpdateResponse,
    ManufacturerSeoUrlUpdateRequest, ManufacturerSeoUrlUpdateResponse,
    ManufacturerLayoutUpdateRequest, ManufacturerLayoutUpdateResponse, ProductListItem,
    StoreInfo, LanguageInfo, SeoUrlItem, LayoutItem, ManufacturerStoreItem
)
from app.services.base_service import BaseService
from app.exceptions import NotFoundException, ConflictException, ValidationException

logger = logging.getLogger(__name__)


class ManufacturerService(BaseService):
    """制造商服务"""
    
    # ==================== 公共方法：查询 ====================
    
    async def list_manufacturers(
        self,
        skip: int = 0,
        limit: int = 20,
        sort: str = "name",
        order: str = "asc",
        filter_name: Optional[str] = None
    ) -> List[ManufacturerListItem]:
        """
        获取制造商列表
        
        Args:
            skip: 跳过的记录数
            limit: 返回的记录数
            sort: 排序字段（name, sort_order）
            order: 排序方向（asc, desc）
            filter_name: 按名称筛选（模糊匹配，不区分大小写）
            
        Returns:
            List[ManufacturerListItem]: 制造商列表
        """
        logger.info(f"开始获取制造商列表: skip={skip}, limit={limit}")
        try:
            query = Manufacturer.all()
            
            # 名称筛选（模糊匹配，不区分大小写）
            # 注意：设计文档要求"模糊匹配"，虽然PHP实现使用前缀匹配，但为了更好的用户体验，使用包含匹配
            if filter_name:
                query = query.filter(name__icontains=filter_name)
            
            # 排序
            sort_field = sort if sort in ["name", "sort_order"] else "name"
            if order == "desc":
                query = query.order_by(f"-{sort_field}")
            else:
                query = query.order_by(sort_field)
            
            manufacturers = await query.offset(skip).limit(limit)
            
            # 构建响应
            result = []
            for manufacturer in manufacturers:
                # 获取商品数量
                product_count = await Product.filter(manufacturer_id=manufacturer.manufacturer_id).count()
                
                item = ManufacturerListItem(
                    manufacturer_id=manufacturer.manufacturer_id,
                    name=manufacturer.name or "",
                    image=manufacturer.image,
                    sort_order=manufacturer.sort_order or 0,
                    product_count=product_count
                )
                result.append(item)
            
            logger.info(f"制造商列表获取完成: count={len(result)}")
            return result
        except Exception as e:
            logger.error(f"获取制造商列表失败: {str(e)}")
            raise
    
    async def get_manufacturer(
        self,
        manufacturer_id: int,
        include_stores: bool = True,
        include_layouts: bool = True,
        include_seo_urls: bool = True,
        include_product_count: bool = True
    ) -> ManufacturerResponse:
        """
        获取制造商详情
        
        Args:
            manufacturer_id: 制造商ID
            include_stores: 是否包含店铺关联
            include_layouts: 是否包含布局关联
            include_seo_urls: 是否包含SEO URL
            include_product_count: 是否包含商品数量
            
        Returns:
            ManufacturerResponse: 制造商信息
            
        Raises:
            NotFoundException: 制造商不存在
        """
        logger.info(f"开始获取制造商详情: manufacturer_id={manufacturer_id}")
        try:
            manufacturer = await Manufacturer.get_or_none(manufacturer_id=manufacturer_id)
            if not manufacturer:
                raise NotFoundException("制造商", manufacturer_id)
            
            response = await self._build_manufacturer_response(
                manufacturer, include_stores, include_layouts, include_seo_urls, include_product_count
            )
            
            logger.info(f"制造商详情获取完成: manufacturer_id={manufacturer_id}")
            return response
        except NotFoundException:
            raise
        except DoesNotExist:
            raise NotFoundException("制造商", manufacturer_id)
        except Exception as e:
            logger.error(f"获取制造商详情失败: manufacturer_id={manufacturer_id}, error={str(e)}")
            raise
    
    async def autocomplete_manufacturers(
        self,
        filter_name: str,
        limit: int = 10
    ) -> List[ManufacturerAutocompleteItem]:
        """
        自动完成制造商名称
        
        Args:
            filter_name: 名称筛选（模糊匹配）
            limit: 返回的记录数（最大50）
            
        Returns:
            List[ManufacturerAutocompleteItem]: 制造商列表
        """
        logger.info(f"开始自动完成制造商: filter_name={filter_name}")
        try:
            if limit > 50:
                limit = 50
            
            query = Manufacturer.filter(name__icontains=filter_name)
            manufacturers = await query.limit(limit)
            
            result = [
                ManufacturerAutocompleteItem(
                    manufacturer_id=m.manufacturer_id,
                    name=m.name or ""
                )
                for m in manufacturers
            ]
            
            logger.info(f"自动完成制造商完成: count={len(result)}")
            return result
        except Exception as e:
            logger.error(f"自动完成制造商失败: {str(e)}")
            raise
    
    # ==================== 公共方法：创建 ====================
    
    async def create_manufacturer(self, data: ManufacturerCreate) -> ManufacturerResponse:
        """
        创建制造商
        
        Args:
            data: 制造商创建数据
            
        Returns:
            ManufacturerResponse: 创建后的制造商信息
            
        Raises:
            ConflictException: 制造商名称已存在
            ValidationException: 验证失败
        """
        logger.info(f"开始创建制造商: name={data.name}")
        try:
            # 常规校验：名称唯一性
            existing = await Manufacturer.filter(name=data.name).first()
            if existing:
                raise ConflictException(f"制造商名称 '{data.name}' 已存在")
            
            # 创建制造商
            manufacturer = await Manufacturer.create(
                name=data.name,
                image=data.image,
                sort_order=data.sort_order or 0
            )
            
            # 处理店铺关联
            store_ids = data.manufacturer_store or [0]
            await self._update_manufacturer_stores(manufacturer.manufacturer_id, store_ids)
            
            # 处理SEO URL
            if data.manufacturer_seo_url:
                await self._update_manufacturer_seo_urls(manufacturer.manufacturer_id, data.manufacturer_seo_url)
            
            # 处理布局
            if data.manufacturer_layout:
                await self._update_manufacturer_layouts(manufacturer.manufacturer_id, data.manufacturer_layout)
            
            logger.info(f"制造商创建完成: manufacturer_id={manufacturer.manufacturer_id}")
            return await self.get_manufacturer(manufacturer.manufacturer_id)
        except (ConflictException, ValidationException):
            raise
        except IntegrityError as e:
            logger.error(f"创建制造商失败: name={data.name}, error={str(e)}")
            raise ConflictException(f"制造商名称 '{data.name}' 已存在")
        except Exception as e:
            logger.error(f"创建制造商失败: name={data.name}, error={str(e)}")
            raise
    
    # ==================== 公共方法：更新 ====================
    
    async def update_manufacturer(
        self,
        manufacturer_id: int,
        data: ManufacturerUpdate
    ) -> ManufacturerResponse:
        """
        更新制造商
        
        Args:
            manufacturer_id: 制造商ID
            data: 制造商更新数据
            
        Returns:
            ManufacturerResponse: 更新后的制造商信息
            
        Raises:
            NotFoundException: 制造商不存在
            ConflictException: 制造商名称冲突
            ValidationException: 验证失败
        """
        logger.info(f"开始更新制造商: manufacturer_id={manufacturer_id}")
        try:
            manufacturer = await Manufacturer.get_or_none(manufacturer_id=manufacturer_id)
            if not manufacturer:
                raise NotFoundException("制造商", manufacturer_id)
            
            update_data = data.model_dump(exclude_unset=True)
            
            # 如果更新名称，检查是否重复
            if 'name' in update_data and update_data['name'] != manufacturer.name:
                existing = await Manufacturer.filter(name=update_data['name']).first()
                if existing and existing.manufacturer_id != manufacturer_id:
                    raise ConflictException(f"制造商名称 '{update_data['name']}' 已存在")
            
            # 更新基础字段
            if 'name' in update_data:
                manufacturer.name = update_data['name']
            if 'image' in update_data:
                manufacturer.image = update_data['image']
            if 'sort_order' in update_data:
                manufacturer.sort_order = update_data['sort_order']
            
            await manufacturer.save()
            
            # 处理店铺关联
            if 'manufacturer_store' in update_data:
                await self._update_manufacturer_stores(manufacturer_id, update_data['manufacturer_store'])
            
            # 处理SEO URL
            if 'manufacturer_seo_url' in update_data:
                await self._update_manufacturer_seo_urls(manufacturer_id, update_data['manufacturer_seo_url'])
            
            # 处理布局
            if 'manufacturer_layout' in update_data:
                await self._update_manufacturer_layouts(manufacturer_id, update_data['manufacturer_layout'])
            
            logger.info(f"制造商更新完成: manufacturer_id={manufacturer_id}")
            return await self.get_manufacturer(manufacturer_id)
        except (NotFoundException, ConflictException, ValidationException):
            raise
        except DoesNotExist:
            raise NotFoundException("制造商", manufacturer_id)
        except Exception as e:
            logger.error(f"更新制造商失败: manufacturer_id={manufacturer_id}, error={str(e)}")
            raise
    
    async def patch_manufacturer(
        self,
        manufacturer_id: int,
        data: ManufacturerPatch
    ) -> ManufacturerResponse:
        """
        部分更新制造商
        
        Args:
            manufacturer_id: 制造商ID
            data: 制造商部分更新数据
            
        Returns:
            ManufacturerResponse: 更新后的制造商信息
            
        Raises:
            NotFoundException: 制造商不存在
            ConflictException: 制造商名称冲突
            ValidationException: 验证失败
        """
        logger.info(f"开始部分更新制造商: manufacturer_id={manufacturer_id}")
        try:
            manufacturer = await Manufacturer.get_or_none(manufacturer_id=manufacturer_id)
            if not manufacturer:
                raise NotFoundException("制造商", manufacturer_id)
            
            update_data = data.model_dump(exclude_unset=True)
            
            if not update_data:
                raise ValidationException("没有需要更新的字段")
            
            # 如果更新名称，检查是否重复
            if 'name' in update_data and update_data['name'] != manufacturer.name:
                existing = await Manufacturer.filter(name=update_data['name']).first()
                if existing and existing.manufacturer_id != manufacturer_id:
                    raise ConflictException(f"制造商名称 '{update_data['name']}' 已存在")
            
            # 更新基础字段
            for key, value in update_data.items():
                if key not in ['manufacturer_store', 'manufacturer_seo_url', 'manufacturer_layout']:
                    setattr(manufacturer, key, value)
            
            await manufacturer.save()
            
            # 处理店铺关联
            if 'manufacturer_store' in update_data:
                await self._update_manufacturer_stores(manufacturer_id, update_data['manufacturer_store'])
            
            # 处理SEO URL
            if 'manufacturer_seo_url' in update_data:
                await self._update_manufacturer_seo_urls(manufacturer_id, update_data['manufacturer_seo_url'])
            
            # 处理布局
            if 'manufacturer_layout' in update_data:
                await self._update_manufacturer_layouts(manufacturer_id, update_data['manufacturer_layout'])
            
            logger.info(f"制造商部分更新完成: manufacturer_id={manufacturer_id}")
            return await self.get_manufacturer(manufacturer_id)
        except (NotFoundException, ConflictException, ValidationException):
            raise
        except DoesNotExist:
            raise NotFoundException("制造商", manufacturer_id)
        except Exception as e:
            logger.error(f"部分更新制造商失败: manufacturer_id={manufacturer_id}, error={str(e)}")
            raise
    
    # ==================== 公共方法：删除 ====================
    
    async def delete_manufacturer(self, manufacturer_id: int) -> None:
        """
        删除制造商
        
        Args:
            manufacturer_id: 制造商ID
            
        Raises:
            NotFoundException: 制造商不存在
            ConflictException: 有商品关联此制造商
        """
        logger.info(f"开始删除制造商: manufacturer_id={manufacturer_id}")
        try:
            manufacturer = await Manufacturer.get_or_none(manufacturer_id=manufacturer_id)
            if not manufacturer:
                raise NotFoundException("制造商", manufacturer_id)
            
            # 逻辑校验：检查是否有商品关联
            product_count = await Product.filter(manufacturer_id=manufacturer_id).count()
            if product_count > 0:
                raise ConflictException(
                    f"无法删除制造商",
                    details={"reason": f"有{product_count}个商品关联此制造商", "product_count": product_count}
                )
            
            # 删除店铺关联
            await self._delete_manufacturer_stores(manufacturer_id)
            
            # 删除布局关联
            await self._delete_manufacturer_layouts(manufacturer_id)
            
            # 删除SEO URL（参照PHP实现）
            await SeoUrl.filter(key="manufacturer_id", value=str(manufacturer_id)).delete()
            
            # 删除制造商
            await manufacturer.delete()
            
            logger.info(f"制造商删除完成: manufacturer_id={manufacturer_id}")
        except (NotFoundException, ConflictException):
            raise
        except DoesNotExist:
            raise NotFoundException("制造商", manufacturer_id)
        except Exception as e:
            logger.error(f"删除制造商失败: manufacturer_id={manufacturer_id}, error={str(e)}")
            raise
    
    async def batch_delete_manufacturers(
        self,
        request: ManufacturerBatchDeleteRequest
    ) -> ManufacturerBatchDeleteResponse:
        """
        批量删除制造商
        
        Args:
            request: 批量删除请求
            
        Returns:
            ManufacturerBatchDeleteResponse: 批量删除结果
        """
        logger.info(f"开始批量删除制造商: ids={request.ids}")
        try:
            results = []
            deleted = 0
            failed = 0
            
            for manufacturer_id in request.ids:
                try:
                    await self.delete_manufacturer(manufacturer_id)
                    results.append({
                        "manufacturer_id": manufacturer_id,
                        "status": "success"
                    })
                    deleted += 1
                except ConflictException as e:
                    results.append({
                        "manufacturer_id": manufacturer_id,
                        "status": "failed",
                        "reason": str(e.detail.get("reason", "有商品关联此制造商") if isinstance(e.detail, dict) else str(e.detail))
                    })
                    failed += 1
                except Exception as e:
                    results.append({
                        "manufacturer_id": manufacturer_id,
                        "status": "failed",
                        "reason": str(e)
                    })
                    failed += 1
            
            logger.info(f"批量删除制造商完成: deleted={deleted}, failed={failed}")
            return ManufacturerBatchDeleteResponse(
                deleted=deleted,
                failed=failed,
                results=results
            )
        except Exception as e:
            logger.error(f"批量删除制造商失败: {str(e)}")
            raise
    
    # ==================== 公共方法：店铺关联 ====================
    
    async def get_manufacturer_stores(
        self,
        manufacturer_id: int
    ) -> List[ManufacturerStoreItem]:
        """
        获取制造商的店铺关联
        
        Args:
            manufacturer_id: 制造商ID
            
        Returns:
            List[ManufacturerStoreItem]: 店铺关联列表
            
        Raises:
            NotFoundException: 制造商不存在
        """
        logger.info(f"开始获取制造商店铺关联: manufacturer_id={manufacturer_id}")
        try:
            # 检查制造商是否存在
            manufacturer = await Manufacturer.get_or_none(manufacturer_id=manufacturer_id)
            if not manufacturer:
                raise NotFoundException("制造商", manufacturer_id)
            
            # 使用values()查询复合主键表（参照开发注意事项）
            store_data_list = await ManufacturerToStore.filter(
                manufacturer_id=manufacturer_id
            ).values('manufacturer_id', 'store_id')
            
            result = []
            for store_data in store_data_list:
                store_id = store_data['store_id']
                store = await Store.get_or_none(store_id=store_id)
                store_info = StoreInfo(
                    store_id=store_id,
                    name=store.name if store else None
                ) if store else None
                
                result.append(ManufacturerStoreItem(
                    store_id=store_id,
                    store=store_info
                ))
            
            logger.info(f"制造商店铺关联获取完成: manufacturer_id={manufacturer_id}, count={len(result)}")
            return result
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"获取制造商店铺关联失败: manufacturer_id={manufacturer_id}, error={str(e)}")
            raise
    
    async def update_manufacturer_stores(
        self,
        manufacturer_id: int,
        request: ManufacturerStoreUpdateRequest
    ) -> ManufacturerStoreUpdateResponse:
        """
        批量更新制造商的店铺关联
        
        Args:
            manufacturer_id: 制造商ID
            request: 店铺更新请求
            
        Returns:
            ManufacturerStoreUpdateResponse: 更新结果
            
        Raises:
            NotFoundException: 制造商不存在
            ValidationException: 验证失败
        """
        logger.info(f"开始更新制造商店铺关联: manufacturer_id={manufacturer_id}")
        try:
            # 检查制造商是否存在
            manufacturer = await Manufacturer.get_or_none(manufacturer_id=manufacturer_id)
            if not manufacturer:
                raise NotFoundException("制造商", manufacturer_id)
            
            # 验证店铺ID是否存在
            for store_id in request.store_ids:
                store = await Store.get_or_none(store_id=store_id)
                if not store and store_id != 0:  # 0是默认店铺，允许
                    raise ValidationException(f"店铺ID {store_id} 不存在")
            
            # 获取现有店铺关联
            existing_data_list = await ManufacturerToStore.filter(
                manufacturer_id=manufacturer_id
            ).values('manufacturer_id', 'store_id')
            existing_store_ids = {item['store_id'] for item in existing_data_list}
            
            new_store_ids = set(request.store_ids)
            
            # 计算新增和删除
            added = len(new_store_ids - existing_store_ids)
            removed = len(existing_store_ids - new_store_ids)
            
            # 删除旧的关联
            await self._delete_manufacturer_stores(manufacturer_id)
            
            # 创建新的关联
            await self._update_manufacturer_stores(manufacturer_id, request.store_ids)
            
            logger.info(f"制造商店铺关联更新完成: manufacturer_id={manufacturer_id}, added={added}, removed={removed}")
            return ManufacturerStoreUpdateResponse(
                added=added,
                removed=removed,
                total=len(new_store_ids)
            )
        except (NotFoundException, ValidationException):
            raise
        except Exception as e:
            logger.error(f"更新制造商店铺关联失败: manufacturer_id={manufacturer_id}, error={str(e)}")
            raise
    
    # ==================== 公共方法：SEO URL ====================
    
    async def get_manufacturer_seo_urls(
        self,
        manufacturer_id: int,
        store_id: Optional[int] = None,
        language_id: Optional[int] = None
    ) -> List[SeoUrlItem]:
        """
        获取制造商的SEO URL列表
        
        Args:
            manufacturer_id: 制造商ID
            store_id: 店铺ID筛选（可选）
            language_id: 语言ID筛选（可选）
            
        Returns:
            List[SeoUrlItem]: SEO URL列表
            
        Raises:
            NotFoundException: 制造商不存在
        """
        logger.info(f"开始获取制造商SEO URL: manufacturer_id={manufacturer_id}")
        try:
            # 检查制造商是否存在
            manufacturer = await Manufacturer.get_or_none(manufacturer_id=manufacturer_id)
            if not manufacturer:
                raise NotFoundException("制造商", manufacturer_id)
            
            query = SeoUrl.filter(key="manufacturer_id", value=str(manufacturer_id))
            
            if store_id is not None:
                query = query.filter(store_id=store_id)
            if language_id is not None:
                query = query.filter(language_id=language_id)
            
            seo_urls = await query.all()
            
            result = []
            for seo_url in seo_urls:
                store = await Store.get_or_none(store_id=seo_url.store_id) if seo_url.store_id else None
                from app.models.localisation.language import Language
                language = await Language.get_or_none(language_id=seo_url.language_id) if seo_url.language_id else None
                
                result.append(SeoUrlItem(
                    seo_url_id=seo_url.seo_url_id,
                    store_id=seo_url.store_id or 0,
                    language_id=seo_url.language_id or 0,
                    keyword=seo_url.keyword or "",
                    store=StoreInfo(
                        store_id=store.store_id,
                        name=store.name
                    ) if store else None,
                    language=LanguageInfo(
                        language_id=language.language_id,
                        name=language.name,
                        code=language.code
                    ) if language else None
                ))
            
            logger.info(f"制造商SEO URL获取完成: manufacturer_id={manufacturer_id}, count={len(result)}")
            return result
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"获取制造商SEO URL失败: manufacturer_id={manufacturer_id}, error={str(e)}")
            raise
    
    async def update_manufacturer_seo_urls(
        self,
        manufacturer_id: int,
        request: ManufacturerSeoUrlUpdateRequest
    ) -> ManufacturerSeoUrlUpdateResponse:
        """
        批量更新制造商的SEO URL
        
        Args:
            manufacturer_id: 制造商ID
            request: SEO URL更新请求
            
        Returns:
            ManufacturerSeoUrlUpdateResponse: 更新结果
            
        Raises:
            NotFoundException: 制造商不存在
            ValidationException: 验证失败
        """
        logger.info(f"开始更新制造商SEO URL: manufacturer_id={manufacturer_id}")
        try:
            # 检查制造商是否存在
            manufacturer = await Manufacturer.get_or_none(manufacturer_id=manufacturer_id)
            if not manufacturer:
                raise NotFoundException("制造商", manufacturer_id)
            
            # 验证SEO URL关键字
            total = 0
            for store_id_str, language_dict in request.seo_urls.items():
                store_id = int(store_id_str)
                for language_id_str, keyword in language_dict.items():
                    language_id = int(language_id_str)
                    
                    # 验证关键字格式
                    if not keyword or len(keyword) < 1 or len(keyword) > 64:
                        raise ValidationException(f"SEO关键字长度必须在1-64字符之间: {keyword}")
                    
                    # 验证关键字格式：只允许字母、数字、连字符和下划线
                    import re
                    if not re.match(r'^[a-zA-Z0-9_-]+$', keyword):
                        raise ValidationException(f"SEO关键字格式不正确，只允许字母、数字、连字符和下划线: {keyword}")
                    
                    # 验证关键字唯一性（在同一店铺和语言下）
                    # 注意：需要排除当前制造商的SEO URL
                    existing_list = await SeoUrl.filter(
                        keyword=keyword,
                        store_id=store_id,
                        language_id=language_id
                    ).all()
                    
                    # 检查是否有其他制造商使用了这个关键字
                    for existing in existing_list:
                        if existing.key == "manufacturer_id" and existing.value != str(manufacturer_id):
                            raise ValidationException(f"SEO关键字 '{keyword}' 已存在（店铺ID: {store_id}, 语言ID: {language_id}）")
                    
                    total += 1
            
            # 删除旧的SEO URL（参照PHP实现）
            await SeoUrl.filter(key="manufacturer_id", value=str(manufacturer_id)).delete()
            
            # 创建新的SEO URL
            for store_id_str, language_dict in request.seo_urls.items():
                store_id = int(store_id_str)
                for language_id_str, keyword in language_dict.items():
                    language_id = int(language_id_str)
                    
                    await SeoUrl.create(
                        store_id=store_id,
                        language_id=language_id,
                        key="manufacturer_id",
                        value=str(manufacturer_id),
                        keyword=keyword,
                        sort_order=0
                    )
            
            logger.info(f"制造商SEO URL更新完成: manufacturer_id={manufacturer_id}, total={total}")
            return ManufacturerSeoUrlUpdateResponse(
                updated=total,
                total=total
            )
        except (NotFoundException, ValidationException):
            raise
        except Exception as e:
            logger.error(f"更新制造商SEO URL失败: manufacturer_id={manufacturer_id}, error={str(e)}")
            raise
    
    # ==================== 公共方法：布局 ====================
    
    async def get_manufacturer_layouts(
        self,
        manufacturer_id: int
    ) -> List[LayoutItem]:
        """
        获取制造商的布局列表
        
        Args:
            manufacturer_id: 制造商ID
            
        Returns:
            List[LayoutItem]: 布局列表
            
        Raises:
            NotFoundException: 制造商不存在
        """
        logger.info(f"开始获取制造商布局: manufacturer_id={manufacturer_id}")
        try:
            # 检查制造商是否存在
            manufacturer = await Manufacturer.get_or_none(manufacturer_id=manufacturer_id)
            if not manufacturer:
                raise NotFoundException("制造商", manufacturer_id)
            
            # 使用values()查询复合主键表
            layout_data_list = await ManufacturerToLayout.filter(
                manufacturer_id=manufacturer_id
            ).values('manufacturer_id', 'store_id', 'layout_id')
            
            result = []
            for layout_data in layout_data_list:
                store_id = layout_data['store_id']
                layout_id = layout_data['layout_id']
                
                store = await Store.get_or_none(store_id=store_id)
                layout = await Layout.get_or_none(layout_id=layout_id)
                
                result.append(LayoutItem(
                    store_id=store_id,
                    layout_id=layout_id,
                    store=StoreInfo(
                        store_id=store.store_id,
                        name=store.name
                    ) if store else None,
                    layout={
                        "layout_id": layout.layout_id,
                        "name": layout.name
                    } if layout else None
                ))
            
            logger.info(f"制造商布局获取完成: manufacturer_id={manufacturer_id}, count={len(result)}")
            return result
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"获取制造商布局失败: manufacturer_id={manufacturer_id}, error={str(e)}")
            raise
    
    async def update_manufacturer_layouts(
        self,
        manufacturer_id: int,
        request: ManufacturerLayoutUpdateRequest
    ) -> ManufacturerLayoutUpdateResponse:
        """
        批量更新制造商的布局
        
        Args:
            manufacturer_id: 制造商ID
            request: 布局更新请求
            
        Returns:
            ManufacturerLayoutUpdateResponse: 更新结果
            
        Raises:
            NotFoundException: 制造商不存在
            ValidationException: 验证失败
        """
        logger.info(f"开始更新制造商布局: manufacturer_id={manufacturer_id}")
        try:
            # 检查制造商是否存在
            manufacturer = await Manufacturer.get_or_none(manufacturer_id=manufacturer_id)
            if not manufacturer:
                raise NotFoundException("制造商", manufacturer_id)
            
            # 验证店铺ID和布局ID
            total = 0
            for store_id_str, layout_id in request.layouts.items():
                store_id = int(store_id_str)
                
                # 验证店铺ID
                if store_id != 0:
                    store = await Store.get_or_none(store_id=store_id)
                    if not store:
                        raise ValidationException(f"店铺ID {store_id} 不存在")
                
                # 验证布局ID（如果layout_id为0或None，表示删除，不需要验证）
                if layout_id and layout_id != 0:
                    layout = await Layout.get_or_none(layout_id=layout_id)
                    if not layout:
                        raise ValidationException(f"布局ID {layout_id} 不存在")
                
                total += 1
            
            # 删除旧的布局关联
            await self._delete_manufacturer_layouts(manufacturer_id)
            
            # 创建新的布局关联（只创建layout_id不为0的）
            for store_id_str, layout_id in request.layouts.items():
                store_id = int(store_id_str)
                if layout_id and layout_id != 0:
                    await ManufacturerToLayout.create(
                        manufacturer_id=manufacturer_id,
                        store_id=store_id,
                        layout_id=layout_id
                    )
            
            logger.info(f"制造商布局更新完成: manufacturer_id={manufacturer_id}, total={total}")
            return ManufacturerLayoutUpdateResponse(
                updated=total,
                total=total
            )
        except (NotFoundException, ValidationException):
            raise
        except Exception as e:
            logger.error(f"更新制造商布局失败: manufacturer_id={manufacturer_id}, error={str(e)}")
            raise
    
    # ==================== 公共方法：商品列表 ====================
    
    async def get_manufacturer_products(
        self,
        manufacturer_id: int,
        skip: int = 0,
        limit: int = 20,
        sort: str = "sort_order",
        order: str = "asc",
        status: Optional[int] = None,
        language_id: Optional[int] = None
    ) -> List[ProductListItem]:
        """
        获取制造商下的商品列表
        
        Args:
            manufacturer_id: 制造商ID
            skip: 跳过的记录数
            limit: 返回的记录数
            sort: 排序字段（name, price, sort_order, date_added）
            order: 排序方向（asc, desc）
            status: 商品状态筛选（0=禁用，1=启用）
            language_id: 语言ID（用于返回对应语言的商品名称）
            
        Returns:
            List[ProductListItem]: 商品列表
            
        Raises:
            NotFoundException: 制造商不存在
        """
        logger.info(f"开始获取制造商商品列表: manufacturer_id={manufacturer_id}")
        try:
            # 检查制造商是否存在
            manufacturer = await Manufacturer.get_or_none(manufacturer_id=manufacturer_id)
            if not manufacturer:
                raise NotFoundException("制造商", manufacturer_id)
            
            query = Product.filter(manufacturer_id=manufacturer_id)
            
            # 状态筛选
            if status is not None:
                query = query.filter(status=status)
            
            # 排序处理
            # 注意：如果按名称排序，需要先获取所有商品，然后通过ProductDescription排序
            if sort == "name":
                # 获取所有商品
                products = await query.all()
                
                # 获取商品名称并排序
                from app.models.catalog.product_description import ProductDescription
                product_names = {}
                if language_id:
                    # 使用指定语言
                    desc_data_list = await ProductDescription.filter(
                        product_id__in=[p.product_id for p in products],
                        language_id=language_id
                    ).values('product_id', 'name')
                    product_names = {desc['product_id']: desc.get('name', '') for desc in desc_data_list}
                else:
                    # 使用第一个可用语言
                    for product in products:
                        desc_data_list = await ProductDescription.filter(
                            product_id=product.product_id
                        ).limit(1).values('name')
                        if desc_data_list:
                            product_names[product.product_id] = desc_data_list[0].get('name', '')
                
                # 按名称排序
                def get_sort_key(product):
                    name = product_names.get(product.product_id, '')
                    return name.lower() if name else ''
                
                products = sorted(products, key=get_sort_key, reverse=(order == "desc"))
                
                # 应用分页
                products = products[skip:skip+limit]
            else:
                # 其他字段直接排序
                sort_field = sort if sort in ["price", "sort_order", "date_added"] else "sort_order"
                if order == "desc":
                    query = query.order_by(f"-{sort_field}")
                else:
                    query = query.order_by(sort_field)
                
                products = await query.offset(skip).limit(limit)
            
            result = []
            for product in products:
                # 获取商品名称（多语言）
                name = None
                if language_id:
                    from app.models.catalog.product_description import ProductDescription
                    desc_data_list = await ProductDescription.filter(
                        product_id=product.product_id,
                        language_id=language_id
                    ).values('name')
                    if desc_data_list:
                        name = desc_data_list[0].get('name')
                else:
                    # 如果没有指定语言，使用第一个可用语言
                    from app.models.catalog.product_description import ProductDescription
                    desc_data_list = await ProductDescription.filter(
                        product_id=product.product_id
                    ).limit(1).values('name')
                    if desc_data_list:
                        name = desc_data_list[0].get('name')
                
                result.append(ProductListItem(
                    product_id=product.product_id,
                    name=name,
                    image=product.image,
                    price=str(product.price) if product.price else None,
                    status=product.status or 0,
                    sort_order=product.sort_order or 0
                ))
            
            logger.info(f"制造商商品列表获取完成: manufacturer_id={manufacturer_id}, count={len(result)}")
            return result
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"获取制造商商品列表失败: manufacturer_id={manufacturer_id}, error={str(e)}")
            raise
    
    # ==================== 私有方法：辅助 ====================
    
    async def _build_manufacturer_response(
        self,
        manufacturer: Manufacturer,
        include_stores: bool = True,
        include_layouts: bool = True,
        include_seo_urls: bool = True,
        include_product_count: bool = True
    ) -> ManufacturerResponse:
        """
        构建制造商响应对象
        
        Args:
            manufacturer: 制造商ORM对象
            include_stores: 是否包含店铺关联
            include_layouts: 是否包含布局关联
            include_seo_urls: 是否包含SEO URL
            include_product_count: 是否包含商品数量
            
        Returns:
            ManufacturerResponse: 制造商响应对象
        """
        stores = None
        if include_stores:
            store_data_list = await ManufacturerToStore.filter(
                manufacturer_id=manufacturer.manufacturer_id
            ).values('store_id')
            stores = [item['store_id'] for item in store_data_list]
        
        layouts = None
        if include_layouts:
            layout_data_list = await ManufacturerToLayout.filter(
                manufacturer_id=manufacturer.manufacturer_id
            ).values('store_id', 'layout_id')
            layouts = {str(item['store_id']): item['layout_id'] for item in layout_data_list}
        
        seo_urls = None
        if include_seo_urls:
            seo_urls = await self.get_manufacturer_seo_urls(manufacturer.manufacturer_id)
        
        product_count = None
        if include_product_count:
            product_count = await Product.filter(manufacturer_id=manufacturer.manufacturer_id).count()
        
        return ManufacturerResponse(
            manufacturer_id=manufacturer.manufacturer_id,
            name=manufacturer.name or "",
            image=manufacturer.image,
            sort_order=manufacturer.sort_order or 0,
            stores=stores,
            layouts=layouts,
            seo_urls=seo_urls,
            product_count=product_count
        )
    
    async def _update_manufacturer_stores(
        self,
        manufacturer_id: int,
        store_ids: List[int]
    ) -> None:
        """
        更新制造商的店铺关联（私有方法）
        
        Args:
            manufacturer_id: 制造商ID
            store_ids: 店铺ID数组
        """
        # 删除旧的关联
        await self._delete_manufacturer_stores(manufacturer_id)
        
        # 创建新的关联（使用values()检查是否存在，避免重复）
        for store_id in store_ids:
            existing_data_list = await ManufacturerToStore.filter(
                manufacturer_id=manufacturer_id,
                store_id=store_id
            ).values('manufacturer_id', 'store_id')
            
            if not existing_data_list:
                await ManufacturerToStore.create(
                    manufacturer_id=manufacturer_id,
                    store_id=store_id
                )
    
    async def _delete_manufacturer_stores(self, manufacturer_id: int) -> None:
        """
        删除制造商的店铺关联（私有方法）
        
        Args:
            manufacturer_id: 制造商ID
        """
        await ManufacturerToStore.filter(manufacturer_id=manufacturer_id).delete()
    
    async def _update_manufacturer_layouts(
        self,
        manufacturer_id: int,
        layouts: Dict[str, int]
    ) -> None:
        """
        更新制造商的布局关联（私有方法）
        
        Args:
            manufacturer_id: 制造商ID
            layouts: 布局对象，格式：{store_id: layout_id}
        """
        # 删除旧的关联
        await self._delete_manufacturer_layouts(manufacturer_id)
        
        # 创建新的关联（只创建layout_id不为0的）
        for store_id_str, layout_id in layouts.items():
            store_id = int(store_id_str)
            if layout_id and layout_id != 0:
                existing_data_list = await ManufacturerToLayout.filter(
                    manufacturer_id=manufacturer_id,
                    store_id=store_id
                ).values('manufacturer_id', 'store_id')
                
                if not existing_data_list:
                    await ManufacturerToLayout.create(
                        manufacturer_id=manufacturer_id,
                        store_id=store_id,
                        layout_id=layout_id
                    )
    
    async def _delete_manufacturer_layouts(self, manufacturer_id: int) -> None:
        """
        删除制造商的布局关联（私有方法）
        
        Args:
            manufacturer_id: 制造商ID
        """
        await ManufacturerToLayout.filter(manufacturer_id=manufacturer_id).delete()
    
    async def _update_manufacturer_seo_urls(
        self,
        manufacturer_id: int,
        seo_urls: Dict[str, Dict[int, str]]
    ) -> None:
        """
        更新制造商的SEO URL（私有方法）
        
        Args:
            manufacturer_id: 制造商ID
            seo_urls: SEO URL对象，格式：{store_id: {language_id: keyword}}
        """
        # 删除旧的SEO URL
        await SeoUrl.filter(key="manufacturer_id", value=str(manufacturer_id)).delete()
        
        # 创建新的SEO URL
        for store_id_str, language_dict in seo_urls.items():
            store_id = int(store_id_str)
            for language_id_str, keyword in language_dict.items():
                language_id = int(language_id_str)
                
                await SeoUrl.create(
                    store_id=store_id,
                    language_id=language_id,
                    key="manufacturer_id",
                    value=str(manufacturer_id),
                    keyword=keyword,
                    sort_order=0
                )

