"""
Currency service - 货币服务层
"""
import logging
import re
from typing import List, Optional
from datetime import datetime
from tortoise.exceptions import DoesNotExist, IntegrityError

try:
    from app.models.localisation.currency import Currency
except (ImportError, AttributeError):
    import importlib
    currency_module = importlib.import_module('app.models.localisation.currency')
    Currency = currency_module.Currency

from app.schemas.currency import CurrencyCreate, CurrencyUpdate, CurrencyResponse
from app.services.base_service import BaseService
from app.exceptions import NotFoundException, ConflictException, ValidationException

logger = logging.getLogger(__name__)


class CurrencyService(BaseService):
    """货币服务"""
    
    async def list_currencies(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[int] = None
    ) -> List[CurrencyResponse]:
        """
        获取货币列表
        
        Args:
            skip: 跳过的记录数
            limit: 返回的记录数
            status: 状态筛选（可选，0=禁用，1=启用）
            
        Returns:
            List[CurrencyResponse]: 货币列表
        """
        logger.info(f"开始获取货币列表: skip={skip}, limit={limit}")
        try:
            query = Currency.all()
            
            if status is not None:
                query = query.filter(status=status)
            
            # 按code和title排序
            currencies = await query.order_by('code', 'title').offset(skip).limit(limit)
            result = [CurrencyResponse.model_validate(currency) for currency in currencies]
            
            logger.info(f"货币列表获取完成: count={len(result)}")
            return result
        except Exception as e:
            logger.error(f"获取货币列表失败: {str(e)}")
            raise
    
    async def get_currency(self, currency_id: int) -> CurrencyResponse:
        """
        根据ID获取货币
        
        Args:
            currency_id: 货币ID
            
        Returns:
            CurrencyResponse: 货币信息
            
        Raises:
            NotFoundException: 货币不存在
        """
        logger.info(f"开始获取货币信息: currency_id={currency_id}")
        try:
            currency = await Currency.get_or_none(currency_id=currency_id)
            if not currency:
                raise NotFoundException("货币", currency_id)
            
            logger.info(f"货币信息获取完成: currency_id={currency_id}")
            return CurrencyResponse.model_validate(currency)
        except NotFoundException:
            raise
        except DoesNotExist:
            raise NotFoundException("货币", currency_id)
        except Exception as e:
            logger.error(f"获取货币信息失败: currency_id={currency_id}, error={str(e)}")
            raise
    
    async def get_currency_by_code(self, code: str) -> CurrencyResponse:
        """
        根据代码获取货币
        
        Args:
            code: 货币代码（如 'USD', 'CNY'）
            
        Returns:
            CurrencyResponse: 货币信息
            
        Raises:
            NotFoundException: 货币不存在
        """
        logger.info(f"开始获取货币: code={code}")
        try:
            # 验证代码格式并转换为大写
            if not await self._validate_code_format(code):
                raise ValidationException(f"无效的货币代码格式: {code}")
            
            code_upper = code.strip().upper()
            # 使用 filter().first() 代替 get_or_none()，避免 Multiple objects returned 错误
            currency = await Currency.filter(code=code_upper).first()
            if not currency:
                raise NotFoundException("货币", 0)
            
            logger.info(f"货币获取完成: currency_id={currency.currency_id}")
            try:
                return CurrencyResponse.model_validate(currency)
            except Exception as validation_error:
                logger.error(f"货币响应验证失败: currency_id={currency.currency_id}, error={str(validation_error)}")
                # 如果验证失败，尝试手动构建响应（绕过验证）
                # 使用 model_construct 可以绕过验证
                return CurrencyResponse.model_construct(
                    currency_id=currency.currency_id,
                    title=currency.title or "",
                    code=currency.code or "",
                    symbol_left=currency.symbol_left,
                    symbol_right=currency.symbol_right,
                    decimal_place=currency.decimal_place or 2,
                    value=currency.value,
                    status=currency.status or 0,
                    date_modified=currency.date_modified
                )
        except (NotFoundException, ValidationException):
            raise
        except Exception as e:
            logger.error(f"获取货币失败: code={code}, error={str(e)}")
            raise
    
    async def create_currency(self, data: CurrencyCreate) -> CurrencyResponse:
        """
        创建新货币
        
        Args:
            data: 货币创建数据
            
        Returns:
            CurrencyResponse: 创建的货币信息
            
        Raises:
            ConflictException: 货币代码已存在
            ValidationException: 验证失败
        """
        logger.info(f"开始创建货币: title={data.title}, code={data.code}")
        try:
            # 验证货币代码格式
            if not await self._validate_code_format(data.code):
                raise ValidationException(f"无效的货币代码格式: {data.code}")
            
            # 检查货币代码是否已存在
            if not await self._validate_code_uniqueness(data.code):
                raise ConflictException(f"货币代码 {data.code} 已存在")
            
            currency = await Currency.create(**data.model_dump())
            logger.info(f"货币创建完成: currency_id={currency.currency_id}, code={data.code}")
            return CurrencyResponse.model_validate(currency)
        except (ConflictException, ValidationException):
            raise
        except IntegrityError as e:
            logger.error(f"创建货币失败（完整性错误）: {str(e)}")
            raise ConflictException(f"创建货币失败: {str(e)}")
        except Exception as e:
            logger.error(f"创建货币失败: {str(e)}")
            raise
    
    async def update_currency(
        self,
        currency_id: int,
        data: CurrencyUpdate
    ) -> CurrencyResponse:
        """
        更新货币
        
        Args:
            currency_id: 货币ID
            data: 货币更新数据
            
        Returns:
            CurrencyResponse: 更新后的货币信息
            
        Raises:
            NotFoundException: 货币不存在
            ConflictException: 货币代码冲突
            ValidationException: 验证失败
        """
        logger.info(f"开始更新货币: currency_id={currency_id}")
        try:
            currency = await Currency.get_or_none(currency_id=currency_id)
            if not currency:
                raise NotFoundException("货币", currency_id)
            
            update_data = data.model_dump(exclude_unset=True)
            
            if not update_data:
                raise ValidationException("没有需要更新的字段")
            
            # 如果更新code，验证格式并检查是否重复
            if 'code' in update_data:
                if not await self._validate_code_format(update_data['code']):
                    raise ValidationException(f"无效的货币代码格式: {update_data['code']}")
                
                if update_data['code'] != currency.code:
                    if not await self._validate_code_uniqueness(update_data['code'], exclude_id=currency_id):
                        raise ConflictException(f"货币代码 {update_data['code']} 已存在")
            
            # 更新字段
            for key, value in update_data.items():
                setattr(currency, key, value)
            
            # 自动更新 date_modified
            currency.date_modified = datetime.now()
            
            await currency.save()
            logger.info(f"货币更新完成: currency_id={currency_id}")
            return CurrencyResponse.model_validate(currency)
        except (NotFoundException, ConflictException, ValidationException):
            raise
        except DoesNotExist:
            raise NotFoundException("货币", currency_id)
        except Exception as e:
            logger.error(f"更新货币失败: currency_id={currency_id}, error={str(e)}")
            raise
    
    async def update_currency_rate(
        self,
        currency_id: int,
        rate: float
    ) -> CurrencyResponse:
        """
        更新货币汇率
        
        Args:
            currency_id: 货币ID
            rate: 新汇率（正数）
            
        Returns:
            CurrencyResponse: 更新后的货币信息
            
        Raises:
            NotFoundException: 货币不存在
            ValidationException: 汇率无效
        """
        logger.info(f"开始更新汇率: currency_id={currency_id}, rate={rate}")
        try:
            if rate < 0:
                raise ValidationException("汇率必须是正数")
            
            currency = await Currency.get_or_none(currency_id=currency_id)
            if not currency:
                raise NotFoundException("货币", currency_id)
            
            currency.value = rate
            # 自动更新 date_modified
            currency.date_modified = datetime.now()
            await currency.save()
            
            logger.info(f"汇率更新完成: currency_id={currency_id}, rate={rate}")
            return CurrencyResponse.model_validate(currency)
        except (NotFoundException, ValidationException):
            raise
        except DoesNotExist:
            raise NotFoundException("货币", currency_id)
        except Exception as e:
            logger.error(f"更新汇率失败: currency_id={currency_id}, error={str(e)}")
            raise
    
    async def delete_currency(self, currency_id: int) -> None:
        """
        删除货币
        
        Args:
            currency_id: 货币ID
            
        Raises:
            NotFoundException: 货币不存在
            ConflictException: 货币被使用，无法删除
        """
        logger.info(f"开始删除货币: currency_id={currency_id}")
        try:
            currency = await Currency.get_or_none(currency_id=currency_id)
            if not currency:
                raise NotFoundException("货币", currency_id)
            
            # 检查是否被使用
            if await self._check_currency_usage(currency_id):
                raise ConflictException(
                    "货币正在被使用，无法删除",
                    details={"currency_id": currency_id}
                )
            
            await currency.delete()
            logger.info(f"货币删除完成: currency_id={currency_id}")
        except (NotFoundException, ConflictException):
            raise
        except DoesNotExist:
            raise NotFoundException("货币", currency_id)
        except Exception as e:
            logger.error(f"删除货币失败: currency_id={currency_id}, error={str(e)}")
            raise
    
    # ==================== 私有方法 ====================
    
    async def _validate_code_uniqueness(
        self,
        code: str,
        exclude_id: Optional[int] = None
    ) -> bool:
        """
        验证货币代码唯一性
        
        Args:
            code: 货币代码
            exclude_id: 排除的货币ID（用于更新时检查）
            
        Returns:
            bool: 如果代码唯一返回True，否则返回False
        """
        try:
            code_upper = code.strip().upper()
            query = Currency.filter(code=code_upper)
            if exclude_id:
                query = query.filter(currency_id__ne=exclude_id)
            
            existing = await query.first()
            return existing is None
        except Exception as e:
            logger.warning(f"验证货币代码唯一性失败: code={code}, error={str(e)}")
            return False
    
    async def _validate_code_format(self, code: str) -> bool:
        """
        验证货币代码格式（ISO 4217）
        
        Args:
            code: 货币代码
            
        Returns:
            bool: 如果格式正确返回True，否则返回False
        """
        if not code:
            return False
        
        code_stripped = code.strip().upper()
        # ISO 4217格式：3个大写字母
        if len(code_stripped) != 3:
            return False
        
        if not re.match(r'^[A-Z]{3}$', code_stripped):
            return False
        
        return True
    
    async def _check_currency_usage(self, currency_id: int) -> bool:
        """
        检查货币是否被使用
        
        Args:
            currency_id: 货币ID
            
        Returns:
            bool: 如果被使用返回True，否则返回False
        """
        try:
            # 获取货币信息
            currency = await Currency.get_or_none(currency_id=currency_id)
            if not currency:
                return False
            
            # 检查订单表是否使用该货币（使用currency_id或currency_code）
            try:
                from app.models.order.order import Order
                # 检查currency_id
                count = await Order.filter(currency_id=currency_id).count()
                if count > 0:
                    logger.info(f"货币被订单使用（currency_id）: currency_id={currency_id}, count={count}")
                    return True
                # 检查currency_code
                if currency.code:
                    count = await Order.filter(currency_code=currency.code).count()
                    if count > 0:
                        logger.info(f"货币被订单使用（currency_code）: currency_id={currency_id}, count={count}")
                        return True
            except (ImportError, AttributeError) as e:
                # 如果订单表不存在，跳过检查
                logger.debug(f"订单表不存在，跳过订单检查: {str(e)}")
            except Exception as e:
                # 如果查询失败（可能是字段不存在），记录警告但继续
                logger.warning(f"检查订单表失败: {str(e)}")
            
            # 可以继续检查其他使用货币的表
            # 例如：交易记录、价格历史等
            
            return False
        except Exception as e:
            logger.warning(f"检查货币使用情况失败: currency_id={currency_id}, error={str(e)}")
            # 如果检查失败，为了安全起见，返回True（不允许删除）
            return True

