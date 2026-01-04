"""
Attribute service - 属性服务层
"""
import logging
from typing import List, Optional
from tortoise.exceptions import DoesNotExist, IntegrityError

try:
    from app.models.catalog.attribute import Attribute
    from app.models.catalog.attribute_description import AttributeDescription
    from app.models.catalog.attribute_group import AttributeGroup
    from app.models.catalog.attribute_group_description import AttributeGroupDescription
    from app.models.catalog.product_attribute import ProductAttribute
    from app.models.localisation.language import Language
except (ImportError, AttributeError):
    import importlib
    attribute_module = importlib.import_module('app.models.catalog.attribute')
    Attribute = attribute_module.Attribute
    attribute_desc_module = importlib.import_module('app.models.catalog.attribute_description')
    AttributeDescription = attribute_desc_module.AttributeDescription
    attribute_group_module = importlib.import_module('app.models.catalog.attribute_group')
    AttributeGroup = attribute_group_module.AttributeGroup
    attribute_group_desc_module = importlib.import_module('app.models.catalog.attribute_group_description')
    AttributeGroupDescription = attribute_group_desc_module.AttributeGroupDescription
    product_attribute_module = importlib.import_module('app.models.catalog.product_attribute')
    ProductAttribute = product_attribute_module.ProductAttribute
    language_module = importlib.import_module('app.models.localisation.language')
    Language = language_module.Language

from app.schemas.attribute import (
    AttributeCreate, AttributeUpdate, AttributeResponse,
    AttributeDescriptionResponse, AttributeDescriptionCreate
)
from app.services.base_service import BaseService
from app.exceptions import NotFoundException, ConflictException, ValidationException

logger = logging.getLogger(__name__)


class AttributeService(BaseService):
    """属性服务"""
    
    async def list_attributes(
        self,
        skip: int = 0,
        limit: int = 20,
        sort: str = "sort_order",
        order: str = "asc",
        filter_name: Optional[str] = None,
        filter_attribute_group_id: Optional[int] = None,
        language_id: Optional[int] = None
    ) -> List[AttributeResponse]:
        """
        获取属性列表
        
        Args:
            skip: 跳过的记录数
            limit: 返回的记录数
            sort: 排序字段（sort_order, attribute_group_id）
            order: 排序方向（asc, desc）
            filter_name: 按名称筛选（模糊匹配）
            filter_attribute_group_id: 按属性组ID筛选
            language_id: 语言ID（用于返回对应语言的名称）
            
        Returns:
            List[AttributeResponse]: 属性列表
        """
        logger.info(f"开始获取属性列表: skip={skip}, limit={limit}")
        try:
            query = Attribute.all()
            
            # 属性组筛选
            if filter_attribute_group_id:
                query = query.filter(attribute_group_id=filter_attribute_group_id)
            
            # 名称筛选
            if filter_name:
                desc_ids = await AttributeDescription.filter(
                    name__icontains=filter_name
                ).values_list('attribute_id', flat=True)
                if desc_ids:
                    query = query.filter(attribute_id__in=desc_ids)
                else:
                    # 如果没有匹配的描述，返回空列表
                    return []
            
            # 排序
            sort_field = sort if sort in ["sort_order", "attribute_group_id"] else "sort_order"
            if order == "desc":
                query = query.order_by(f"-{sort_field}")
            else:
                query = query.order_by(sort_field)
            
            attributes = await query.offset(skip).limit(limit)
            
            # 构建响应
            result = []
            for attribute in attributes:
                response = await self._build_attribute_response(attribute, language_id)
                result.append(response)
            
            logger.info(f"属性列表获取完成: count={len(result)}")
            return result
        except Exception as e:
            logger.error(f"获取属性列表失败: {str(e)}")
            raise
    
    async def get_attribute(
        self,
        attribute_id: int,
        language_id: Optional[int] = None
    ) -> AttributeResponse:
        """
        获取属性详情
        
        Args:
            attribute_id: 属性ID
            language_id: 语言ID（用于返回对应语言的名称）
            
        Returns:
            AttributeResponse: 属性信息
            
        Raises:
            NotFoundException: 属性不存在
        """
        logger.info(f"开始获取属性详情: attribute_id={attribute_id}")
        try:
            attribute = await Attribute.get_or_none(attribute_id=attribute_id)
            if not attribute:
                raise NotFoundException("属性", attribute_id)
            
            response = await self._build_attribute_response(attribute, language_id)
            logger.info(f"属性详情获取完成: attribute_id={attribute_id}")
            return response
        except NotFoundException:
            raise
        except DoesNotExist:
            raise NotFoundException("属性", attribute_id)
        except Exception as e:
            logger.error(f"获取属性详情失败: attribute_id={attribute_id}, error={str(e)}")
            raise
    
    async def create_attribute(
        self,
        data: AttributeCreate
    ) -> AttributeResponse:
        """
        创建属性
        
        Args:
            data: 属性创建数据
            
        Returns:
            AttributeResponse: 创建的属性信息
            
        Raises:
            ValidationException: 验证失败
            NotFoundException: 属性组不存在
        """
        logger.info("开始创建属性")
        try:
            # 验证属性组是否存在
            group = await AttributeGroup.get_or_none(attribute_group_id=data.attribute_group_id)
            if not group:
                raise ValidationException(f"属性组ID {data.attribute_group_id} 不存在")
            
            # 验证描述数据
            if not data.descriptions or len(data.descriptions) == 0:
                raise ValidationException("至少需要提供一个语言描述")
            
            # 检查语言ID是否重复
            language_ids = [desc.language_id for desc in data.descriptions]
            if len(language_ids) != len(set(language_ids)):
                raise ValidationException("描述中的语言ID不能重复")
            
            # 验证语言是否存在
            for desc in data.descriptions:
                language = await Language.get_or_none(language_id=desc.language_id)
                if not language:
                    raise ValidationException(f"语言ID {desc.language_id} 不存在")
            
            # 创建属性
            attribute = await Attribute.create(
                attribute_group_id=data.attribute_group_id,
                sort_order=data.sort_order or 0
            )
            
            # 创建描述
            for desc_data in data.descriptions:
                await AttributeDescription.create(
                    attribute_id=attribute.attribute_id,
                    language_id=desc_data.language_id,
                    name=desc_data.name
                )
            
            # 构建响应
            response = await self._build_attribute_response(attribute)
            
            logger.info(f"属性创建完成: attribute_id={attribute.attribute_id}")
            return response
        except (ValidationException, NotFoundException, ConflictException):
            raise
        except IntegrityError as e:
            logger.error(f"创建属性失败（完整性错误）: {str(e)}")
            raise ConflictException(f"创建属性失败: {str(e)}")
        except Exception as e:
            logger.error(f"创建属性失败: {str(e)}")
            raise
    
    async def update_attribute(
        self,
        attribute_id: int,
        data: AttributeCreate
    ) -> AttributeResponse:
        """
        完整更新属性
        
        Args:
            attribute_id: 属性ID
            data: 属性更新数据
            
        Returns:
            AttributeResponse: 更新后的属性信息
            
        Raises:
            NotFoundException: 属性或属性组不存在
            ValidationException: 验证失败
        """
        logger.info(f"开始更新属性: attribute_id={attribute_id}")
        try:
            attribute = await Attribute.get_or_none(attribute_id=attribute_id)
            if not attribute:
                raise NotFoundException("属性", attribute_id)
            
            # 验证属性组是否存在（如果改变了属性组）
            if data.attribute_group_id != attribute.attribute_group_id:
                group = await AttributeGroup.get_or_none(attribute_group_id=data.attribute_group_id)
                if not group:
                    raise ValidationException(f"属性组ID {data.attribute_group_id} 不存在")
            
            # 验证描述数据
            if not data.descriptions or len(data.descriptions) == 0:
                raise ValidationException("至少需要提供一个语言描述")
            
            # 检查语言ID是否重复
            language_ids = [desc.language_id for desc in data.descriptions]
            if len(language_ids) != len(set(language_ids)):
                raise ValidationException("描述中的语言ID不能重复")
            
            # 验证语言是否存在
            for desc in data.descriptions:
                language = await Language.get_or_none(language_id=desc.language_id)
                if not language:
                    raise ValidationException(f"语言ID {desc.language_id} 不存在")
            
            # 更新属性
            attribute.attribute_group_id = data.attribute_group_id
            attribute.sort_order = data.sort_order or 0
            await attribute.save()
            
            # 删除旧描述
            await AttributeDescription.filter(attribute_id=attribute_id).delete()
            
            # 创建新描述
            for desc_data in data.descriptions:
                await AttributeDescription.create(
                    attribute_id=attribute.attribute_id,
                    language_id=desc_data.language_id,
                    name=desc_data.name
                )
            
            # 构建响应
            response = await self._build_attribute_response(attribute)
            
            logger.info(f"属性更新完成: attribute_id={attribute_id}")
            return response
        except (NotFoundException, ValidationException, ConflictException):
            raise
        except DoesNotExist:
            raise NotFoundException("属性", attribute_id)
        except Exception as e:
            logger.error(f"更新属性失败: attribute_id={attribute_id}, error={str(e)}")
            raise
    
    async def patch_attribute(
        self,
        attribute_id: int,
        data: AttributeUpdate
    ) -> AttributeResponse:
        """
        部分更新属性
        
        Args:
            attribute_id: 属性ID
            data: 属性更新数据
            
        Returns:
            AttributeResponse: 更新后的属性信息
            
        Raises:
            NotFoundException: 属性或属性组不存在
            ValidationException: 验证失败
        """
        logger.info(f"开始部分更新属性: attribute_id={attribute_id}")
        try:
            attribute = await Attribute.get_or_none(attribute_id=attribute_id)
            if not attribute:
                raise NotFoundException("属性", attribute_id)
            
            update_data = data.model_dump(exclude_unset=True)
            
            if not update_data:
                raise ValidationException("没有需要更新的字段")
            
            # 更新属性字段
            if 'attribute_group_id' in update_data:
                # 验证属性组是否存在
                group = await AttributeGroup.get_or_none(attribute_group_id=data.attribute_group_id)
                if not group:
                    raise ValidationException(f"属性组ID {data.attribute_group_id} 不存在")
                attribute.attribute_group_id = data.attribute_group_id
            
            if 'sort_order' in update_data:
                attribute.sort_order = data.sort_order
                await attribute.save()
            elif 'attribute_group_id' in update_data:
                await attribute.save()
            
            # 更新描述（如果提供）
            if data.descriptions is not None:
                # 验证描述数据
                if len(data.descriptions) == 0:
                    raise ValidationException("描述数组不能为空")
                
                # 检查语言ID是否重复
                language_ids = [desc.language_id for desc in data.descriptions]
                if len(language_ids) != len(set(language_ids)):
                    raise ValidationException("描述中的语言ID不能重复")
                
                # 验证语言是否存在
                for desc in data.descriptions:
                    language = await Language.get_or_none(language_id=desc.language_id)
                    if not language:
                        raise ValidationException(f"语言ID {desc.language_id} 不存在")
                
                # 删除旧描述
                await AttributeDescription.filter(attribute_id=attribute_id).delete()
                
                # 创建新描述
                for desc_data in data.descriptions:
                    await AttributeDescription.create(
                        attribute_id=attribute.attribute_id,
                        language_id=desc_data.language_id,
                        name=desc_data.name
                    )
            
            # 构建响应
            response = await self._build_attribute_response(attribute)
            
            logger.info(f"属性部分更新完成: attribute_id={attribute_id}")
            return response
        except (NotFoundException, ValidationException, ConflictException):
            raise
        except DoesNotExist:
            raise NotFoundException("属性", attribute_id)
        except Exception as e:
            logger.error(f"部分更新属性失败: attribute_id={attribute_id}, error={str(e)}")
            raise
    
    async def delete_attribute(self, attribute_id: int) -> None:
        """
        删除属性
        
        Args:
            attribute_id: 属性ID
            
        Raises:
            NotFoundException: 属性不存在
            ConflictException: 属性被商品使用，无法删除
        """
        logger.info(f"开始删除属性: attribute_id={attribute_id}")
        try:
            attribute = await Attribute.get_or_none(attribute_id=attribute_id)
            if not attribute:
                raise NotFoundException("属性", attribute_id)
            
            # 检查是否被商品使用
            product_count = await ProductAttribute.filter(attribute_id=attribute_id).count()
            if product_count > 0:
                raise ConflictException(
                    "属性已被商品使用，无法删除",
                    details={"product_count": product_count}
                )
            
            # 删除描述
            await AttributeDescription.filter(attribute_id=attribute_id).delete()
            
            # 删除属性
            await attribute.delete()
            
            logger.info(f"属性删除完成: attribute_id={attribute_id}")
        except (NotFoundException, ConflictException):
            raise
        except DoesNotExist:
            raise NotFoundException("属性", attribute_id)
        except Exception as e:
            logger.error(f"删除属性失败: attribute_id={attribute_id}, error={str(e)}")
            raise
    
    async def get_attribute_group_attributes(
        self,
        group_id: int,
        language_id: Optional[int] = None,
        sort: str = "sort_order",
        order: str = "asc"
    ) -> List[AttributeResponse]:
        """
        获取属性组下的所有属性
        
        Args:
            group_id: 属性组ID
            language_id: 语言ID（用于返回对应语言的名称）
            sort: 排序字段
            order: 排序方向
            
        Returns:
            List[AttributeResponse]: 属性列表
            
        Raises:
            NotFoundException: 属性组不存在
        """
        logger.info(f"开始获取属性组下的属性: group_id={group_id}")
        try:
            # 验证属性组是否存在
            group = await AttributeGroup.get_or_none(attribute_group_id=group_id)
            if not group:
                raise NotFoundException("属性组", group_id)
            
            query = Attribute.filter(attribute_group_id=group_id)
            
            # 排序
            sort_field = sort if sort in ["sort_order"] else "sort_order"
            if order == "desc":
                query = query.order_by(f"-{sort_field}")
            else:
                query = query.order_by(sort_field)
            
            attributes = await query.all()
            
            # 构建响应
            result = []
            for attribute in attributes:
                response = await self._build_attribute_response(attribute, language_id)
                result.append(response)
            
            logger.info(f"属性组下的属性获取完成: group_id={group_id}, count={len(result)}")
            return result
        except NotFoundException:
            raise
        except DoesNotExist:
            raise NotFoundException("属性组", group_id)
        except Exception as e:
            logger.error(f"获取属性组下的属性失败: group_id={group_id}, error={str(e)}")
            raise
    
    # ==================== 私有方法 ====================
    
    async def _get_language_code(self, language_id: int) -> Optional[str]:
        """
        获取语言代码
        
        Args:
            language_id: 语言ID
            
        Returns:
            Optional[str]: 语言代码
        """
        try:
            language = await Language.get_or_none(language_id=language_id)
            return language.code if language else None
        except Exception:
            return None
    
    async def _get_attribute_group_name(
        self,
        attribute_group_id: int,
        language_id: Optional[int] = None
    ) -> Optional[str]:
        """
        获取属性组名称
        
        Args:
            attribute_group_id: 属性组ID
            language_id: 语言ID
            
        Returns:
            Optional[str]: 属性组名称
        """
        try:
            if language_id:
                desc_data_list = await AttributeGroupDescription.filter(
                    attribute_group_id=attribute_group_id,
                    language_id=language_id
                ).limit(1).values('name')
                if desc_data_list:
                    return desc_data_list[0]['name']
            # 如果没有指定语言，返回第一个描述
            desc_data_list = await AttributeGroupDescription.filter(
                attribute_group_id=attribute_group_id
            ).limit(1).values('name')
            return desc_data_list[0]['name'] if desc_data_list else None
        except Exception:
            return None
    
    async def _build_attribute_response(
        self,
        attribute: Attribute,
        language_id: Optional[int] = None
    ) -> AttributeResponse:
        """
        构建属性响应对象
        
        Args:
            attribute: Attribute模型实例
            language_id: 语言ID（用于返回对应语言的名称）
            
        Returns:
            AttributeResponse: 属性响应对象
        """
        # 获取所有描述（使用 values() 方法避免选择不存在的 'id' 字段）
        descriptions_data = await AttributeDescription.filter(
            attribute_id=attribute.attribute_id
        ).values('attribute_id', 'language_id', 'name')
        
        # 手动构建描述对象列表
        descriptions = []
        for desc_data in descriptions_data:
            desc = AttributeDescription()
            desc.attribute_id = desc_data['attribute_id']
            desc.language_id = desc_data['language_id']
            desc.name = desc_data['name']
            descriptions.append(desc)
        
        # 构建描述响应
        desc_responses = []
        for desc in descriptions:
            lang_code = await self._get_language_code(desc.language_id)
            desc_responses.append(AttributeDescriptionResponse(
                language_id=desc.language_id,
                language_code=lang_code,
                name=desc.name or ""
            ))
        
        # 获取属性组名称
        attribute_group_name = await self._get_attribute_group_name(
            attribute.attribute_group_id,
            language_id
        )
        
        # 获取当前语言的名称
        name = None
        if language_id:
            desc_data_list = await AttributeDescription.filter(
                attribute_id=attribute.attribute_id,
                language_id=language_id
            ).limit(1).values('name')
            if desc_data_list:
                name = desc_data_list[0]['name']
        
        return AttributeResponse(
            attribute_id=attribute.attribute_id,
            attribute_group_id=attribute.attribute_group_id,
            sort_order=attribute.sort_order or 0,
            descriptions=desc_responses,
            attribute_group_name=attribute_group_name,
            name=name
        )

