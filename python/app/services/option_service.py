"""
Option service - 选项服务层
"""
import logging
from typing import List, Optional
from tortoise.exceptions import DoesNotExist, IntegrityError

try:
    from app.models.catalog.option import Option
    from app.models.catalog.option_description import OptionDescription
    from app.models.catalog.option_value import OptionValue
    from app.models.catalog.option_value_description import OptionValueDescription
    from app.models.catalog.product_option import ProductOption
    from app.models.localisation.language import Language
except (ImportError, AttributeError):
    import importlib
    option_module = importlib.import_module('app.models.catalog.option')
    Option = option_module.Option
    option_desc_module = importlib.import_module('app.models.catalog.option_description')
    OptionDescription = option_desc_module.OptionDescription
    option_value_module = importlib.import_module('app.models.catalog.option_value')
    OptionValue = option_value_module.OptionValue
    option_value_desc_module = importlib.import_module('app.models.catalog.option_value_description')
    OptionValueDescription = option_value_desc_module.OptionValueDescription
    product_option_module = importlib.import_module('app.models.catalog.product_option')
    ProductOption = product_option_module.ProductOption
    language_module = importlib.import_module('app.models.localisation.language')
    Language = language_module.Language

from app.schemas.option import (
    OptionCreate, OptionUpdate, OptionResponse,
    OptionDescriptionResponse, OptionDescriptionCreate
)
from app.services.base_service import BaseService
from app.exceptions import NotFoundException, ConflictException, ValidationException

logger = logging.getLogger(__name__)


class OptionService(BaseService):
    """选项服务"""
    
    async def list_options(
        self,
        skip: int = 0,
        limit: int = 20,
        sort: str = "sort_order",
        order: str = "asc",
        filter_name: Optional[str] = None,
        filter_type: Optional[str] = None,
        language_id: Optional[int] = None
    ) -> List[OptionResponse]:
        """
        获取选项列表
        
        Args:
            skip: 跳过的记录数
            limit: 返回的记录数
            sort: 排序字段（sort_order）
            order: 排序方向（asc, desc）
            filter_name: 按名称筛选（模糊匹配）
            filter_type: 按选项类型筛选
            language_id: 语言ID（用于返回对应语言的名称）
            
        Returns:
            List[OptionResponse]: 选项列表
        """
        logger.info(f"开始获取选项列表: skip={skip}, limit={limit}")
        try:
            query = Option.all()
            
            # 类型筛选
            if filter_type:
                query = query.filter(type=filter_type)
            
            # 名称筛选
            if filter_name:
                desc_ids = await OptionDescription.filter(
                    name__icontains=filter_name
                ).values_list('option_id', flat=True)
                if desc_ids:
                    query = query.filter(option_id__in=desc_ids)
                else:
                    # 如果没有匹配的描述，返回空列表
                    return []
            
            # 排序
            sort_field = sort if sort in ["sort_order"] else "sort_order"
            if order == "desc":
                query = query.order_by(f"-{sort_field}")
            else:
                query = query.order_by(sort_field)
            
            options = await query.offset(skip).limit(limit)
            
            # 构建响应
            result = []
            for option in options:
                response = await self._build_option_response(option, language_id)
                result.append(response)
            
            logger.info(f"选项列表获取完成: count={len(result)}")
            return result
        except Exception as e:
            logger.error(f"获取选项列表失败: {str(e)}")
            raise
    
    async def get_option(
        self,
        option_id: int,
        language_id: Optional[int] = None,
        include_values: bool = False
    ) -> OptionResponse:
        """
        获取选项详情
        
        Args:
            option_id: 选项ID
            language_id: 语言ID（用于返回对应语言的名称）
            include_values: 是否包含选项值列表
            
        Returns:
            OptionResponse: 选项信息
            
        Raises:
            NotFoundException: 选项不存在
        """
        logger.info(f"开始获取选项详情: option_id={option_id}")
        try:
            option = await Option.get_or_none(option_id=option_id)
            if not option:
                raise NotFoundException("选项", option_id)
            
            response = await self._build_option_response(option, language_id, include_values)
            logger.info(f"选项详情获取完成: option_id={option_id}")
            return response
        except NotFoundException:
            raise
        except DoesNotExist:
            raise NotFoundException("选项", option_id)
        except Exception as e:
            logger.error(f"获取选项详情失败: option_id={option_id}, error={str(e)}")
            raise
    
    async def create_option(
        self,
        data: OptionCreate
    ) -> OptionResponse:
        """
        创建选项
        
        Args:
            data: 选项创建数据
            
        Returns:
            OptionResponse: 创建的选项信息
            
        Raises:
            ValidationException: 验证失败
            ConflictException: 创建失败
        """
        logger.info(f"开始创建选项: type={data.type}")
        try:
            # 验证描述数据
            if not data.descriptions or len(data.descriptions) == 0:
                raise ValidationException("至少需要提供一个语言描述")
            
            # 检查语言ID是否重复
            language_ids = [desc.language_id for desc in data.descriptions]
            if len(language_ids) != len(set(language_ids)):
                raise ValidationException("描述中的语言ID不能重复")
            
            # 验证语言是否存在和名称长度
            for desc in data.descriptions:
                # 验证语言是否存在
                language = await Language.filter(language_id=desc.language_id).first()
                if not language:
                    raise ValidationException(f"语言ID {desc.language_id} 不存在")
                
                # 验证名称长度和内容（参照PHP实现：oc_validate_length($value['name'], 1, 128)）
                if not desc.name or len(desc.name.strip()) == 0:
                    raise ValidationException(f"语言ID {desc.language_id} 的名称不能为空")
                if len(desc.name) > 128:
                    raise ValidationException(f"语言ID {desc.language_id} 的名称长度不能超过128个字符")
            
            # 创建选项
            option = await Option.create(
                type=data.type,
                validation=data.validation,
                sort_order=data.sort_order or 0
            )
            
            # 创建描述
            for desc_data in data.descriptions:
                await OptionDescription.create(
                    option_id=option.option_id,
                    language_id=desc_data.language_id,
                    name=desc_data.name
                )
            
            # 构建响应
            response = await self._build_option_response(option)
            
            logger.info(f"选项创建完成: option_id={option.option_id}")
            return response
        except (ValidationException, ConflictException):
            raise
        except IntegrityError as e:
            logger.error(f"创建选项失败（完整性错误）: {str(e)}")
            raise ConflictException(f"创建选项失败: {str(e)}")
        except Exception as e:
            logger.error(f"创建选项失败: {str(e)}")
            raise
    
    async def update_option(
        self,
        option_id: int,
        data: OptionCreate
    ) -> OptionResponse:
        """
        完整更新选项
        
        Args:
            option_id: 选项ID
            data: 选项更新数据
            
        Returns:
            OptionResponse: 更新后的选项信息
            
        Raises:
            NotFoundException: 选项不存在
            ValidationException: 验证失败
        """
        logger.info(f"开始更新选项: option_id={option_id}")
        try:
            option = await Option.get_or_none(option_id=option_id)
            if not option:
                raise NotFoundException("选项", option_id)
            
            # 验证描述数据
            if not data.descriptions or len(data.descriptions) == 0:
                raise ValidationException("至少需要提供一个语言描述")
            
            # 检查语言ID是否重复
            language_ids = [desc.language_id for desc in data.descriptions]
            if len(language_ids) != len(set(language_ids)):
                raise ValidationException("描述中的语言ID不能重复")
            
            # 验证语言是否存在和名称长度
            for desc in data.descriptions:
                # 验证语言是否存在
                language = await Language.filter(language_id=desc.language_id).first()
                if not language:
                    raise ValidationException(f"语言ID {desc.language_id} 不存在")
                
                # 验证名称长度和内容（参照PHP实现：oc_validate_length($value['name'], 1, 128)）
                if not desc.name or len(desc.name.strip()) == 0:
                    raise ValidationException(f"语言ID {desc.language_id} 的名称不能为空")
                if len(desc.name) > 128:
                    raise ValidationException(f"语言ID {desc.language_id} 的名称长度不能超过128个字符")
            
            # 如果类型改变为 select/radio/checkbox，检查是否已有选项值（参照PHP实现）
            if data.type in ['select', 'radio', 'checkbox']:
                value_count = await OptionValue.filter(option_id=option_id).count()
                if value_count == 0:
                    raise ValidationException(
                        f"选项类型 '{data.type}' 必须至少有一个选项值。请先创建选项值。"
                    )
            
            # 更新选项
            option.type = data.type
            option.validation = data.validation
            option.sort_order = data.sort_order or 0
            await option.save()
            
            # 删除旧描述
            await OptionDescription.filter(option_id=option_id).delete()
            
            # 创建新描述
            for desc_data in data.descriptions:
                await OptionDescription.create(
                    option_id=option.option_id,
                    language_id=desc_data.language_id,
                    name=desc_data.name
                )
            
            # 构建响应
            response = await self._build_option_response(option)
            
            logger.info(f"选项更新完成: option_id={option_id}")
            return response
        except (NotFoundException, ValidationException):
            raise
        except DoesNotExist:
            raise NotFoundException("选项", option_id)
        except Exception as e:
            logger.error(f"更新选项失败: option_id={option_id}, error={str(e)}")
            raise
    
    async def patch_option(
        self,
        option_id: int,
        data: OptionUpdate
    ) -> OptionResponse:
        """
        部分更新选项
        
        Args:
            option_id: 选项ID
            data: 选项更新数据
            
        Returns:
            OptionResponse: 更新后的选项信息
            
        Raises:
            NotFoundException: 选项不存在
            ValidationException: 验证失败
        """
        logger.info(f"开始部分更新选项: option_id={option_id}")
        try:
            option = await Option.get_or_none(option_id=option_id)
            if not option:
                raise NotFoundException("选项", option_id)
            
            update_data = data.model_dump(exclude_unset=True)
            
            if not update_data:
                raise ValidationException("没有需要更新的字段")
            
            # 更新选项字段
            if 'type' in update_data:
                option.type = data.type
            if 'validation' in update_data:
                option.validation = data.validation
            if 'sort_order' in update_data:
                option.sort_order = data.sort_order
            
            await option.save()
            
            # 更新描述（如果提供）
            if data.descriptions is not None:
                # 验证描述数据
                if len(data.descriptions) == 0:
                    raise ValidationException("描述数组不能为空")
                
                # 检查语言ID是否重复
                language_ids = [desc.language_id for desc in data.descriptions]
                if len(language_ids) != len(set(language_ids)):
                    raise ValidationException("描述中的语言ID不能重复")
                
                # 验证语言是否存在和名称长度
                for desc in data.descriptions:
                    # 验证语言是否存在
                    language = await Language.filter(language_id=desc.language_id).first()
                    if not language:
                        raise ValidationException(f"语言ID {desc.language_id} 不存在")
                    
                    # 验证名称长度和内容（参照PHP实现：oc_validate_length($value['name'], 1, 128)）
                    if not desc.name or len(desc.name.strip()) == 0:
                        raise ValidationException(f"语言ID {desc.language_id} 的名称不能为空")
                    if len(desc.name) > 128:
                        raise ValidationException(f"语言ID {desc.language_id} 的名称长度不能超过128个字符")
                
                # 删除旧描述
                await OptionDescription.filter(option_id=option_id).delete()
                
                # 创建新描述
                for desc_data in data.descriptions:
                    await OptionDescription.create(
                        option_id=option.option_id,
                        language_id=desc_data.language_id,
                        name=desc_data.name
                    )
            
            # 构建响应
            response = await self._build_option_response(option)
            
            logger.info(f"选项部分更新完成: option_id={option_id}")
            return response
        except (NotFoundException, ValidationException):
            raise
        except DoesNotExist:
            raise NotFoundException("选项", option_id)
        except Exception as e:
            logger.error(f"部分更新选项失败: option_id={option_id}, error={str(e)}")
            raise
    
    async def delete_option(self, option_id: int) -> None:
        """
        删除选项
        
        Args:
            option_id: 选项ID
            
        Raises:
            NotFoundException: 选项不存在
            ConflictException: 选项被商品使用，无法删除
        """
        logger.info(f"开始删除选项: option_id={option_id}")
        try:
            option = await Option.get_or_none(option_id=option_id)
            if not option:
                raise NotFoundException("选项", option_id)
            
            # 检查是否被商品使用
            product_count = await ProductOption.filter(option_id=option_id).count()
            if product_count > 0:
                raise ConflictException(
                    "选项已被商品使用，无法删除",
                    details={"product_count": product_count}
                )
            
            # 获取选项值ID列表
            option_values = await OptionValue.filter(option_id=option_id).values_list('option_value_id', flat=True)
            
            # 删除选项值描述
            if option_values:
                await OptionValueDescription.filter(option_value_id__in=option_values).delete()
            
            # 删除选项值
            await OptionValue.filter(option_id=option_id).delete()
            
            # 删除描述
            await OptionDescription.filter(option_id=option_id).delete()
            
            # 删除选项
            await option.delete()
            
            logger.info(f"选项删除完成: option_id={option_id}")
        except (NotFoundException, ConflictException):
            raise
        except DoesNotExist:
            raise NotFoundException("选项", option_id)
        except Exception as e:
            logger.error(f"删除选项失败: option_id={option_id}, error={str(e)}")
            raise
    
    # ==================== 私有方法 ====================
    
    async def _get_option_name(
        self,
        option_id: int,
        language_id: Optional[int] = None
    ) -> Optional[str]:
        """
        获取选项名称
        
        Args:
            option_id: 选项ID
            language_id: 语言ID
            
        Returns:
            Optional[str]: 选项名称
        """
        try:
            if language_id:
                desc_data_list = await OptionDescription.filter(
                    option_id=option_id,
                    language_id=language_id
                ).limit(1).values('name')
                if desc_data_list:
                    return desc_data_list[0]['name']
            # 如果没有指定语言，返回第一个描述
            desc_data_list = await OptionDescription.filter(
                option_id=option_id
            ).limit(1).values('name')
            return desc_data_list[0]['name'] if desc_data_list else None
        except Exception:
            return None
    
    async def _build_option_response(
        self,
        option: Option,
        language_id: Optional[int] = None,
        include_values: bool = False
    ) -> OptionResponse:
        """
        构建选项响应对象
        
        Args:
            option: Option模型实例
            language_id: 语言ID（用于返回对应语言的名称）
            include_values: 是否包含选项值列表
            
        Returns:
            OptionResponse: 选项响应对象
        """
        # 获取所有描述（使用 values() 方法避免选择不存在的 'id' 字段）
        descriptions_data = await OptionDescription.filter(
            option_id=option.option_id
        ).values('option_id', 'language_id', 'name')
        
        # 手动构建描述对象列表
        descriptions = []
        for desc_data in descriptions_data:
            desc = OptionDescription()
            desc.option_id = desc_data['option_id']
            desc.language_id = desc_data['language_id']
            desc.name = desc_data['name']
            descriptions.append(desc)
        
        # 构建描述响应
        desc_responses = []
        for desc in descriptions:
            lang_code = await self.get_language_code(desc.language_id)
            desc_responses.append(OptionDescriptionResponse(
                language_id=desc.language_id,
                language_code=lang_code,
                name=desc.name or ""
            ))
        
        # 获取选项值数量
        value_count = await OptionValue.filter(option_id=option.option_id).count()
        
        # 获取当前语言的名称
        name = None
        if language_id:
            desc_data_list = await OptionDescription.filter(
                option_id=option.option_id,
                language_id=language_id
            ).limit(1).values('name')
            if desc_data_list:
                name = desc_data_list[0]['name']
        
        return OptionResponse(
            option_id=option.option_id,
            type=option.type or "",
            validation=option.validation,
            sort_order=option.sort_order or 0,
            descriptions=desc_responses,
            value_count=value_count,
            name=name
        )

