"""
OptionValue service - 选项值服务层
"""
import logging
from typing import List, Optional, Dict, Any
from tortoise.exceptions import DoesNotExist, IntegrityError

try:
    from app.models.catalog.option_value import OptionValue
    from app.models.catalog.option_value_description import OptionValueDescription
    from app.models.catalog.option import Option
    from app.models.catalog.product_option_value import ProductOptionValue
    from app.models.localisation.language import Language
except (ImportError, AttributeError):
    import importlib
    option_value_module = importlib.import_module('app.models.catalog.option_value')
    OptionValue = option_value_module.OptionValue
    option_value_desc_module = importlib.import_module('app.models.catalog.option_value_description')
    OptionValueDescription = option_value_desc_module.OptionValueDescription
    option_module = importlib.import_module('app.models.catalog.option')
    Option = option_module.Option
    product_option_value_module = importlib.import_module('app.models.catalog.product_option_value')
    ProductOptionValue = product_option_value_module.ProductOptionValue
    language_module = importlib.import_module('app.models.localisation.language')
    Language = language_module.Language

from app.schemas.option_value import (
    OptionValueCreate, OptionValueUpdate, OptionValueResponse,
    OptionValueDescriptionResponse, OptionValueDescriptionCreate, OptionValueSortUpdate
)
from app.services.base_service import BaseService
from app.exceptions import NotFoundException, ConflictException, ValidationException

logger = logging.getLogger(__name__)


class OptionValueService(BaseService):
    """选项值服务"""
    
    async def get_option_value(
        self,
        option_value_id: int,
        language_id: Optional[int] = None
    ) -> OptionValueResponse:
        """
        获取选项值详情
        
        Args:
            option_value_id: 选项值ID
            language_id: 语言ID（用于返回对应语言的名称）
            
        Returns:
            OptionValueResponse: 选项值信息
            
        Raises:
            NotFoundException: 选项值不存在
        """
        logger.info(f"开始获取选项值详情: option_value_id={option_value_id}")
        try:
            option_value = await OptionValue.get_or_none(option_value_id=option_value_id)
            if not option_value:
                raise NotFoundException("选项值", option_value_id)
            
            response = await self._build_option_value_response(option_value, language_id)
            logger.info(f"选项值详情获取完成: option_value_id={option_value_id}")
            return response
        except NotFoundException:
            raise
        except DoesNotExist:
            raise NotFoundException("选项值", option_value_id)
        except Exception as e:
            logger.error(f"获取选项值详情失败: option_value_id={option_value_id}, error={str(e)}")
            raise
    
    async def create_option_value(
        self,
        data: OptionValueCreate
    ) -> OptionValueResponse:
        """
        创建选项值
        
        Args:
            data: 选项值创建数据
            
        Returns:
            OptionValueResponse: 创建的选项值信息
            
        Raises:
            NotFoundException: 选项不存在
            ValidationException: 验证失败
            ConflictException: 创建失败
        """
        logger.info(f"开始创建选项值: option_id={data.option_id}")
        try:
            # 验证选项是否存在
            option = await Option.filter(option_id=data.option_id).first()
            if not option:
                raise NotFoundException("选项", data.option_id)
            
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
                
                # 验证名称长度和内容（参照PHP实现：oc_validate_length($option_value_description['name'], 1, 128)）
                if not desc.name or len(desc.name.strip()) == 0:
                    raise ValidationException(f"语言ID {desc.language_id} 的名称不能为空")
                if len(desc.name) > 128:
                    raise ValidationException(f"语言ID {desc.language_id} 的名称长度不能超过128个字符")
            
            # 创建选项值
            option_value = await OptionValue.create(
                option_id=data.option_id,
                image=data.image,
                sort_order=data.sort_order or 0
            )
            
            # 创建描述
            for desc_data in data.descriptions:
                await OptionValueDescription.create(
                    option_value_id=option_value.option_value_id,
                    language_id=desc_data.language_id,
                    option_id=data.option_id,
                    name=desc_data.name
                )
            
            # 构建响应
            response = await self._build_option_value_response(option_value)
            
            logger.info(f"选项值创建完成: option_value_id={option_value.option_value_id}")
            return response
        except (NotFoundException, ValidationException, ConflictException):
            raise
        except IntegrityError as e:
            logger.error(f"创建选项值失败（完整性错误）: {str(e)}")
            raise ConflictException(f"创建选项值失败: {str(e)}")
        except Exception as e:
            logger.error(f"创建选项值失败: {str(e)}")
            raise
    
    async def update_option_value(
        self,
        option_value_id: int,
        data: OptionValueCreate
    ) -> OptionValueResponse:
        """
        完整更新选项值
        
        Args:
            option_value_id: 选项值ID
            data: 选项值更新数据
            
        Returns:
            OptionValueResponse: 更新后的选项值信息
            
        Raises:
            NotFoundException: 选项值或选项不存在
            ValidationException: 验证失败
        """
        logger.info(f"开始更新选项值: option_value_id={option_value_id}")
        try:
            option_value = await OptionValue.get_or_none(option_value_id=option_value_id)
            if not option_value:
                raise NotFoundException("选项值", option_value_id)
            
            # 验证选项是否存在（如果改变了选项）
            if data.option_id != option_value.option_id:
                option = await Option.filter(option_id=data.option_id).first()
                if not option:
                    raise NotFoundException("选项", data.option_id)
            
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
                
                # 验证名称长度和内容（参照PHP实现：oc_validate_length($option_value_description['name'], 1, 128)）
                if not desc.name or len(desc.name.strip()) == 0:
                    raise ValidationException(f"语言ID {desc.language_id} 的名称不能为空")
                if len(desc.name) > 128:
                    raise ValidationException(f"语言ID {desc.language_id} 的名称长度不能超过128个字符")
            
            # 更新选项值
            option_value.option_id = data.option_id
            option_value.image = data.image
            option_value.sort_order = data.sort_order or 0
            await option_value.save()
            
            # 删除旧描述
            await OptionValueDescription.filter(option_value_id=option_value_id).delete()
            
            # 创建新描述
            for desc_data in data.descriptions:
                await OptionValueDescription.create(
                    option_value_id=option_value.option_value_id,
                    language_id=desc_data.language_id,
                    option_id=data.option_id,
                    name=desc_data.name
                )
            
            # 构建响应
            response = await self._build_option_value_response(option_value)
            
            logger.info(f"选项值更新完成: option_value_id={option_value_id}")
            return response
        except (NotFoundException, ValidationException):
            raise
        except DoesNotExist:
            raise NotFoundException("选项值", option_value_id)
        except Exception as e:
            logger.error(f"更新选项值失败: option_value_id={option_value_id}, error={str(e)}")
            raise
    
    async def patch_option_value(
        self,
        option_value_id: int,
        data: OptionValueUpdate
    ) -> OptionValueResponse:
        """
        部分更新选项值
        
        Args:
            option_value_id: 选项值ID
            data: 选项值更新数据
            
        Returns:
            OptionValueResponse: 更新后的选项值信息
            
        Raises:
            NotFoundException: 选项值或选项不存在
            ValidationException: 验证失败
        """
        logger.info(f"开始部分更新选项值: option_value_id={option_value_id}")
        try:
            option_value = await OptionValue.get_or_none(option_value_id=option_value_id)
            if not option_value:
                raise NotFoundException("选项值", option_value_id)
            
            update_data = data.model_dump(exclude_unset=True)
            
            if not update_data:
                raise ValidationException("没有需要更新的字段")
            
            # 更新选项值字段
            if 'option_id' in update_data:
                # 验证选项是否存在
                option = await Option.filter(option_id=data.option_id).first()
                if not option:
                    raise NotFoundException("选项", data.option_id)
                option_value.option_id = data.option_id
            
            if 'image' in update_data:
                option_value.image = data.image
            if 'sort_order' in update_data:
                option_value.sort_order = data.sort_order
            
            await option_value.save()
            
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
                    
                    # 验证名称长度和内容（参照PHP实现：oc_validate_length($option_value_description['name'], 1, 128)）
                    if not desc.name or len(desc.name.strip()) == 0:
                        raise ValidationException(f"语言ID {desc.language_id} 的名称不能为空")
                    if len(desc.name) > 128:
                        raise ValidationException(f"语言ID {desc.language_id} 的名称长度不能超过128个字符")
                
                # 删除旧描述
                await OptionValueDescription.filter(option_value_id=option_value_id).delete()
                
                # 创建新描述
                for desc_data in data.descriptions:
                    await OptionValueDescription.create(
                        option_value_id=option_value.option_value_id,
                        language_id=desc_data.language_id,
                        option_id=option_value.option_id,
                        name=desc_data.name
                    )
            
            # 构建响应
            response = await self._build_option_value_response(option_value)
            
            logger.info(f"选项值部分更新完成: option_value_id={option_value_id}")
            return response
        except (NotFoundException, ValidationException):
            raise
        except DoesNotExist:
            raise NotFoundException("选项值", option_value_id)
        except Exception as e:
            logger.error(f"部分更新选项值失败: option_value_id={option_value_id}, error={str(e)}")
            raise
    
    async def delete_option_value(self, option_value_id: int) -> None:
        """
        删除选项值
        
        Args:
            option_value_id: 选项值ID
            
        Raises:
            NotFoundException: 选项值不存在
            ConflictException: 选项值被商品使用，无法删除
        """
        logger.info(f"开始删除选项值: option_value_id={option_value_id}")
        try:
            option_value = await OptionValue.get_or_none(option_value_id=option_value_id)
            if not option_value:
                raise NotFoundException("选项值", option_value_id)
            
            # 检查是否被商品使用
            product_count = await ProductOptionValue.filter(option_value_id=option_value_id).count()
            if product_count > 0:
                raise ConflictException(
                    "选项值已被商品使用，无法删除",
                    details={"product_count": product_count}
                )
            
            # 检查删除后选项是否还有选项值（参照PHP实现：选项类型为select/radio/checkbox时必须至少保留一个选项值）
            option = await Option.filter(option_id=option_value.option_id).first()
            if option and option.type in ['select', 'radio', 'checkbox']:
                remaining_count = await OptionValue.filter(
                    option_id=option_value.option_id
                ).count()
                if remaining_count <= 1:  # 当前要删除的是最后一个
                    raise ConflictException(
                        f"选项类型 '{option.type}' 必须至少保留一个选项值，无法删除"
                    )
            
            # 删除描述
            await OptionValueDescription.filter(option_value_id=option_value_id).delete()
            
            # 删除选项值
            await option_value.delete()
            
            logger.info(f"选项值删除完成: option_value_id={option_value_id}")
        except (NotFoundException, ConflictException):
            raise
        except DoesNotExist:
            raise NotFoundException("选项值", option_value_id)
        except Exception as e:
            logger.error(f"删除选项值失败: option_value_id={option_value_id}, error={str(e)}")
            raise
    
    async def get_option_values(
        self,
        option_id: int,
        language_id: Optional[int] = None,
        sort: str = "sort_order",
        order: str = "asc"
    ) -> List[OptionValueResponse]:
        """
        获取选项下的所有选项值
        
        Args:
            option_id: 选项ID
            language_id: 语言ID（用于返回对应语言的名称）
            sort: 排序字段
            order: 排序方向
            
        Returns:
            List[OptionValueResponse]: 选项值列表
            
        Raises:
            NotFoundException: 选项不存在
        """
        logger.info(f"开始获取选项下的选项值: option_id={option_id}")
        try:
            # 验证选项是否存在
            option = await Option.filter(option_id=option_id).first()
            if not option:
                raise NotFoundException("选项", option_id)
            
            query = OptionValue.filter(option_id=option_id)
            
            # 排序
            sort_field = sort if sort in ["sort_order"] else "sort_order"
            if order == "desc":
                query = query.order_by(f"-{sort_field}")
            else:
                query = query.order_by(sort_field)
            
            option_values = await query.all()
            
            # 构建响应
            result = []
            for option_value in option_values:
                response = await self._build_option_value_response(option_value, language_id)
                result.append(response)
            
            logger.info(f"选项下的选项值获取完成: option_id={option_id}, count={len(result)}")
            return result
        except NotFoundException:
            raise
        except DoesNotExist:
            raise NotFoundException("选项", option_id)
        except Exception as e:
            logger.error(f"获取选项下的选项值失败: option_id={option_id}, error={str(e)}")
            raise
    
    async def create_option_value_for_option(
        self,
        option_id: int,
        data: OptionValueCreate
    ) -> OptionValueResponse:
        """
        为选项创建选项值
        
        Args:
            option_id: 选项ID（路径参数）
            data: 选项值创建数据
            
        Returns:
            OptionValueResponse: 创建的选项值信息
            
        Raises:
            NotFoundException: 选项不存在
            ValidationException: 验证失败
        """
        logger.info(f"开始为选项创建选项值: option_id={option_id}")
        try:
            # 验证选项是否存在
            option = await Option.filter(option_id=option_id).first()
            if not option:
                raise NotFoundException("选项", option_id)
            
            # 确保option_id一致
            if data.option_id != option_id:
                raise ValidationException("路径参数中的option_id与请求体中的option_id不一致")
            
            # 创建选项值（复用create_option_value方法）
            return await self.create_option_value(data)
        except (NotFoundException, ValidationException):
            raise
        except Exception as e:
            logger.error(f"为选项创建选项值失败: option_id={option_id}, error={str(e)}")
            raise
    
    async def update_option_values_sort(
        self,
        option_id: int,
        sort_data: OptionValueSortUpdate
    ) -> Dict[str, Any]:
        """
        批量更新选项值的排序
        
        Args:
            option_id: 选项ID
            sort_data: 排序数据
            
        Returns:
            Dict[str, Any]: 更新结果
            
        Raises:
            NotFoundException: 选项不存在
            ValidationException: 验证失败
        """
        logger.info(f"开始批量更新选项值排序: option_id={option_id}")
        try:
            # 验证选项是否存在
            option = await Option.filter(option_id=option_id).first()
            if not option:
                raise NotFoundException("选项", option_id)
            
            # 批量更新排序
            for value_data in sort_data.values:
                option_value_id = value_data.get("option_value_id")
                sort_order = value_data.get("sort_order")
                
                if option_value_id and sort_order is not None:
                    option_value = await OptionValue.filter(
                        option_value_id=option_value_id,
                        option_id=option_id
                    ).first()
                    if option_value:
                        option_value.sort_order = sort_order
                        await option_value.save()
            
            logger.info(f"选项值排序更新完成: option_id={option_id}")
            return {"success": True, "message": "排序更新成功", "data": None}
        except (NotFoundException, ValidationException):
            raise
        except DoesNotExist:
            raise NotFoundException("选项", option_id)
        except Exception as e:
            logger.error(f"批量更新选项值排序失败: option_id={option_id}, error={str(e)}")
            raise
    
    # ==================== 私有方法 ====================
    
    async def _get_option_value_name(
        self,
        option_value_id: int,
        language_id: Optional[int] = None
    ) -> Optional[str]:
        """
        获取选项值名称
        
        Args:
            option_value_id: 选项值ID
            language_id: 语言ID
            
        Returns:
            Optional[str]: 选项值名称
        """
        try:
            if language_id:
                desc_data_list = await OptionValueDescription.filter(
                    option_value_id=option_value_id,
                    language_id=language_id
                ).limit(1).values('name')
                if desc_data_list:
                    return desc_data_list[0]['name']
            # 如果没有指定语言，返回第一个描述
            desc_data_list = await OptionValueDescription.filter(
                option_value_id=option_value_id
            ).limit(1).values('name')
            return desc_data_list[0]['name'] if desc_data_list else None
        except Exception:
            return None
    
    async def _build_option_value_response(
        self,
        option_value: OptionValue,
        language_id: Optional[int] = None
    ) -> OptionValueResponse:
        """
        构建选项值响应对象
        
        Args:
            option_value: OptionValue模型实例
            language_id: 语言ID（用于返回对应语言的名称）
            
        Returns:
            OptionValueResponse: 选项值响应对象
        """
        # 获取所有描述（使用 values() 方法避免选择不存在的 'id' 字段）
        descriptions_data = await OptionValueDescription.filter(
            option_value_id=option_value.option_value_id
        ).values('option_value_id', 'language_id', 'option_id', 'name')
        
        # 手动构建描述对象列表
        descriptions = []
        for desc_data in descriptions_data:
            desc = OptionValueDescription()
            desc.option_value_id = desc_data['option_value_id']
            desc.language_id = desc_data['language_id']
            desc.option_id = desc_data['option_id']
            desc.name = desc_data['name']
            descriptions.append(desc)
        
        # 构建描述响应
        desc_responses = []
        for desc in descriptions:
            lang_code = await self.get_language_code(desc.language_id)
            desc_responses.append(OptionValueDescriptionResponse(
                language_id=desc.language_id,
                language_code=lang_code,
                name=desc.name or ""
            ))
        
        # 获取当前语言的名称
        name = None
        if language_id:
            desc_data_list = await OptionValueDescription.filter(
                option_value_id=option_value.option_value_id,
                language_id=language_id
            ).limit(1).values('name')
            if desc_data_list:
                name = desc_data_list[0]['name']
        
        return OptionValueResponse(
            option_value_id=option_value.option_value_id,
            option_id=option_value.option_id,
            image=option_value.image,
            sort_order=option_value.sort_order or 0,
            descriptions=desc_responses,
            name=name
        )

