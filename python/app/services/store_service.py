"""
Store service - 店铺服务层
"""
import logging
from typing import List, Optional
from urllib.parse import urlparse
from tortoise.exceptions import DoesNotExist, IntegrityError

try:
    from app.models.system.store import Store
except (ImportError, AttributeError):
    import importlib
    store_module = importlib.import_module('app.models.system.store')
    Store = store_module.Store

from app.schemas.store import StoreCreate, StoreUpdate, StoreResponse
from app.services.base_service import BaseService
from app.exceptions import NotFoundException, ConflictException, ValidationException

logger = logging.getLogger(__name__)


class StoreService(BaseService):
    """店铺服务"""
    
    async def list_stores(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[StoreResponse]:
        """
        获取店铺列表
        
        Args:
            skip: 跳过的记录数
            limit: 返回的记录数
            
        Returns:
            List[StoreResponse]: 店铺列表
        """
        logger.info(f"开始获取店铺列表: skip={skip}, limit={limit}")
        try:
            stores = await Store.all().offset(skip).limit(limit)
            result = [StoreResponse.model_validate(store) for store in stores]
            
            logger.info(f"店铺列表获取完成: count={len(result)}")
            return result
        except Exception as e:
            logger.error(f"获取店铺列表失败: {str(e)}")
            raise
    
    async def get_store(self, store_id: int) -> StoreResponse:
        """
        根据ID获取店铺
        
        Args:
            store_id: 店铺ID
            
        Returns:
            StoreResponse: 店铺信息
            
        Raises:
            NotFoundException: 店铺不存在
        """
        logger.info(f"开始获取店铺信息: store_id={store_id}")
        try:
            store = await Store.get_or_none(store_id=store_id)
            if not store:
                raise NotFoundException("店铺", store_id)
            
            logger.info(f"店铺信息获取完成: store_id={store_id}")
            return StoreResponse.model_validate(store)
        except NotFoundException:
            raise
        except DoesNotExist:
            raise NotFoundException("店铺", store_id)
        except Exception as e:
            logger.error(f"获取店铺信息失败: store_id={store_id}, error={str(e)}")
            raise
    
    async def create_store(self, data: StoreCreate) -> StoreResponse:
        """
        创建新店铺
        
        Args:
            data: 店铺创建数据
            
        Returns:
            StoreResponse: 创建的店铺信息
            
        Raises:
            ConflictException: 店铺名称已存在
            ValidationException: 验证失败
        """
        logger.info(f"开始创建店铺: name={data.name}")
        try:
            # 验证URL格式
            if not await self._validate_url(data.url):
                raise ValidationException(f"无效的URL格式: {data.url}")
            
            # 检查店铺名称是否已存在
            if not await self._validate_name_uniqueness(data.name):
                raise ConflictException(f"店铺名称 {data.name} 已存在")
            
            store = await Store.create(**data.model_dump())
            logger.info(f"店铺创建完成: store_id={store.store_id}, name={data.name}")
            return StoreResponse.model_validate(store)
        except (ConflictException, ValidationException):
            raise
        except IntegrityError as e:
            logger.error(f"创建店铺失败（完整性错误）: {str(e)}")
            raise ConflictException(f"创建店铺失败: {str(e)}")
        except Exception as e:
            logger.error(f"创建店铺失败: {str(e)}")
            raise
    
    async def update_store(
        self,
        store_id: int,
        data: StoreUpdate
    ) -> StoreResponse:
        """
        更新店铺
        
        Args:
            store_id: 店铺ID
            data: 店铺更新数据
            
        Returns:
            StoreResponse: 更新后的店铺信息
            
        Raises:
            NotFoundException: 店铺不存在
            ConflictException: 店铺名称冲突
            ValidationException: 验证失败
        """
        logger.info(f"开始更新店铺: store_id={store_id}")
        try:
            store = await Store.get_or_none(store_id=store_id)
            if not store:
                raise NotFoundException("店铺", store_id)
            
            update_data = data.model_dump(exclude_unset=True)
            
            if not update_data:
                raise ValidationException("没有需要更新的字段")
            
            # 如果更新URL，验证格式
            if 'url' in update_data:
                if not await self._validate_url(update_data['url']):
                    raise ValidationException(f"无效的URL格式: {update_data['url']}")
            
            # 如果更新名称，检查是否重复
            if 'name' in update_data and update_data['name'] != store.name:
                if not await self._validate_name_uniqueness(update_data['name'], exclude_id=store_id):
                    raise ConflictException(f"店铺名称 {update_data['name']} 已存在")
            
            # 更新字段
            for key, value in update_data.items():
                setattr(store, key, value)
            
            await store.save()
            logger.info(f"店铺更新完成: store_id={store_id}")
            return StoreResponse.model_validate(store)
        except (NotFoundException, ConflictException, ValidationException):
            raise
        except DoesNotExist:
            raise NotFoundException("店铺", store_id)
        except Exception as e:
            logger.error(f"更新店铺失败: store_id={store_id}, error={str(e)}")
            raise
    
    async def delete_store(self, store_id: int) -> None:
        """
        删除店铺
        
        Args:
            store_id: 店铺ID
            
        Raises:
            NotFoundException: 店铺不存在
            ConflictException: 店铺被使用，无法删除
        """
        logger.info(f"开始删除店铺: store_id={store_id}")
        try:
            store = await Store.get_or_none(store_id=store_id)
            if not store:
                raise NotFoundException("店铺", store_id)
            
            # 检查是否被使用
            if await self._check_store_usage(store_id):
                raise ConflictException(
                    "店铺正在被使用，无法删除",
                    details={"store_id": store_id}
                )
            
            await store.delete()
            logger.info(f"店铺删除完成: store_id={store_id}")
        except (NotFoundException, ConflictException):
            raise
        except DoesNotExist:
            raise NotFoundException("店铺", store_id)
        except Exception as e:
            logger.error(f"删除店铺失败: store_id={store_id}, error={str(e)}")
            raise
    
    # ==================== 私有方法 ====================
    
    async def _validate_name_uniqueness(
        self,
        name: str,
        exclude_id: Optional[int] = None
    ) -> bool:
        """
        验证店铺名称唯一性
        
        Args:
            name: 店铺名称
            exclude_id: 排除的店铺ID（用于更新时检查）
            
        Returns:
            bool: 如果名称唯一返回True，否则返回False
        """
        try:
            query = Store.filter(name=name)
            if exclude_id:
                query = query.filter(store_id__ne=exclude_id)
            
            existing = await query.first()
            return existing is None
        except Exception as e:
            logger.warning(f"验证店铺名称唯一性失败: name={name}, error={str(e)}")
            return False
    
    async def _validate_url(self, url: str) -> bool:
        """
        验证URL格式
        
        Args:
            url: URL字符串
            
        Returns:
            bool: 如果URL格式正确返回True，否则返回False
        """
        if not url:
            return False
        
        try:
            result = urlparse(url)
            # 基本URL验证：必须有scheme和netloc
            if not result.scheme or not result.netloc:
                return False
            
            # 验证scheme必须是http或https
            if result.scheme not in ['http', 'https']:
                return False
            
            return True
        except Exception:
            return False
    
    async def _check_store_usage(self, store_id: int) -> bool:
        """
        检查店铺是否被使用
        
        Args:
            store_id: 店铺ID
            
        Returns:
            bool: 如果被使用返回True，否则返回False
        """
        try:
            # 检查设置表是否使用该店铺
            try:
                from app.models.system.setting import Setting
                count = await Setting.filter(store_id=store_id).count()
                if count > 0:
                    logger.info(f"店铺被设置使用: store_id={store_id}, count={count}")
                    return True
            except (ImportError, AttributeError):
                logger.debug("设置表不存在，跳过设置检查")
            
            # 检查订单表是否使用该店铺
            try:
                from app.models.sale.order import Order
                count = await Order.filter(store_id=store_id).count()
                if count > 0:
                    logger.info(f"店铺被订单使用: store_id={store_id}, count={count}")
                    return True
            except (ImportError, AttributeError):
                logger.debug("订单表不存在，跳过订单检查")
            
            # 检查商品表是否使用该店铺
            try:
                from app.models.catalog.product_to_store import ProductToStore
                count = await ProductToStore.filter(store_id=store_id).count()
                if count > 0:
                    logger.info(f"店铺被商品使用: store_id={store_id}, count={count}")
                    return True
            except (ImportError, AttributeError):
                logger.debug("商品店铺关联表不存在，跳过商品检查")
            
            # 可以继续检查其他使用店铺的表
            # 例如：分类、用户等
            
            return False
        except Exception as e:
            logger.warning(f"检查店铺使用情况失败: store_id={store_id}, error={str(e)}")
            # 如果检查失败，为了安全起见，返回True（不允许删除）
            return True

