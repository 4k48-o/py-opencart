"""
ProductAttributeService - 商品属性关联服务

参照PHP实现：
- php/upload/admin/model/catalog/product.php (addAttribute, deleteAttributes, getAttributes)
"""

import logging
from typing import List, Dict, Any, Optional
from app.models.catalog.product import Product
from app.models.catalog.product_attribute import ProductAttribute
from app.models.catalog.attribute import Attribute
from app.models.catalog.attribute_group import AttributeGroup
from app.schemas.product import (
    ProductAttributeCreate,
    ProductAttributeResponse,
    ProductAttributeDescriptionResponse
)
from app.exceptions import NotFoundException, ValidationException
from app.models.localisation.language import Language

logger = logging.getLogger(__name__)


class ProductAttributeService:
    """商品属性关联服务"""
    
    async def list_product_attributes(
        self,
        product_id: int,
        language_id: Optional[int] = None
    ) -> List[ProductAttributeResponse]:
        """
        获取商品属性列表（参照PHP getAttributes）
        
        PHP实现逻辑：
        1. 先按attribute_id分组，按attribute_group和attribute的sort_order排序
        2. 为每个attribute_id获取所有语言的描述
        3. 返回包含product_attribute_description的数据结构
        
        Args:
            product_id: 商品ID
            language_id: 可选，指定语言ID（用于返回text字段）
            
        Returns:
            List[ProductAttributeResponse]: 商品属性列表
        """
        try:
            # 验证商品存在
            product = await Product.get_or_none(product_id=product_id)
            if not product:
                raise NotFoundException("商品不存在", {"product_id": f"商品ID {product_id} 不存在"})
            
            # 获取所有唯一的attribute_id（参照PHP：GROUP BY attribute_id）
            # 注意：ProductAttribute使用复合主键，需要使用values()避免访问不存在的id字段
            attribute_ids_data = await ProductAttribute.filter(
                product_id=product_id
            ).values('attribute_id')
            
            # 去重获取唯一的attribute_id
            attribute_ids = list(set([item['attribute_id'] for item in attribute_ids_data if item['attribute_id']]))
            
            if not attribute_ids:
                return []
            
            # 获取属性信息并排序（参照PHP：ORDER BY ag.sort_order ASC, a.sort_order ASC）
            attributes_data = await Attribute.filter(
                attribute_id__in=attribute_ids
            ).all()
            
            # 获取AttributeGroup信息（用于排序）
            from app.models.catalog.attribute_group import AttributeGroup
            attribute_group_ids = list(set([attr.attribute_group_id for attr in attributes_data if attr.attribute_group_id]))
            attribute_groups = {}
            if attribute_group_ids:
                groups = await AttributeGroup.filter(attribute_group_id__in=attribute_group_ids).all()
                attribute_groups = {g.attribute_group_id: g for g in groups}
            
            # 创建attribute_id到attribute的映射
            attribute_map = {attr.attribute_id: attr for attr in attributes_data}
            
            # 按sort_order排序（参照PHP：ORDER BY ag.sort_order ASC, a.sort_order ASC）
            def get_sort_key(aid):
                attr = attribute_map.get(aid)
                if not attr:
                    return (0, 0)
                ag = attribute_groups.get(attr.attribute_group_id) if attr.attribute_group_id else None
                ag_sort = ag.sort_order if ag else 0
                attr_sort = attr.sort_order if attr else 0
                return (ag_sort, attr_sort)
            
            sorted_attribute_ids = sorted(attribute_ids, key=get_sort_key)
            
            result = []
            
            # 为每个attribute_id获取所有语言的描述（参照PHP逻辑）
            for attribute_id in sorted_attribute_ids:
                attribute = attribute_map.get(attribute_id)
                if not attribute:
                    continue
                
                # 获取该attribute_id的所有语言描述
                descriptions_data = await ProductAttribute.filter(
                    product_id=product_id,
                    attribute_id=attribute_id
                ).values('language_id', 'text')
                
                # 构建多语言描述列表
                descriptions = []
                current_text = None
                
                for desc_data in descriptions_data:
                    lang_id = desc_data['language_id']
                    text = desc_data.get('text', '')
                    
                    # 获取语言信息
                    language = await Language.get_or_none(language_id=lang_id)
                    
                    descriptions.append(ProductAttributeDescriptionResponse(
                        language_id=lang_id,
                        language_code=language.code if language else None,
                        text=text
                    ))
                    
                    # 如果是指定语言，设置当前文本
                    if language_id and lang_id == language_id:
                        current_text = text
                
                # 如果没有指定language_id，使用第一个描述作为text
                if not current_text and descriptions:
                    current_text = descriptions[0].text
                
                # 获取属性信息
                attribute_info = None
                if attribute:
                    attribute_info = {
                        "attribute_id": attribute.attribute_id,
                        "attribute_group_id": attribute.attribute_group_id,
                        "sort_order": attribute.sort_order
                    }
                
                result.append(ProductAttributeResponse(
                    attribute_id=attribute_id,
                    attribute=attribute_info,
                    text=current_text,
                    descriptions=descriptions
                ))
            
            logger.info(f"获取商品属性列表成功: product_id={product_id}, count={len(result)}")
            return result
            
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"获取商品属性列表失败: product_id={product_id}, error={str(e)}")
            raise
    
    async def add_product_attribute(
        self,
        product_id: int,
        attribute_id: int,
        language_id: int,
        text: str
    ) -> None:
        """
        添加商品属性（参照PHP addAttribute）
        
        PHP实现：
        INSERT INTO product_attribute SET product_id, attribute_id, language_id, text
        
        Args:
            product_id: 商品ID
            attribute_id: 属性ID
            language_id: 语言ID
            text: 属性文本
        """
        try:
            # 验证商品存在
            product = await Product.get_or_none(product_id=product_id)
            if not product:
                raise NotFoundException("商品不存在", {"product_id": f"商品ID {product_id} 不存在"})
            
            # 验证属性存在（验证错误应返回ValidationException，而不是NotFoundException）
            attribute = await Attribute.get_or_none(attribute_id=attribute_id)
            if not attribute:
                raise ValidationException("属性不存在", {"attribute_id": f"属性ID {attribute_id} 不存在"})
            
            # 验证属性组存在性（参照PHP：属性必须属于某个属性组）
            if attribute.attribute_group_id and attribute.attribute_group_id > 0:
                from app.models.catalog.attribute_group import AttributeGroup
                attribute_group = await AttributeGroup.get_or_none(attribute_group_id=attribute.attribute_group_id)
                if not attribute_group:
                    raise ValidationException("属性组不存在", {"attribute_group_id": f"属性组ID {attribute.attribute_group_id} 不存在"})
            
            # 验证语言存在
            language = await Language.get_or_none(language_id=language_id)
            if not language:
                raise ValidationException("语言不存在", {"language_id": f"语言ID {language_id} 不存在"})
            
            # 验证文本长度
            if len(text) > 65535:
                raise ValidationException("属性文本过长", {"text": "属性文本长度不能超过65535字符"})
            
            # 检查是否已存在（参照PHP：先删除再添加，避免重复）
            # 注意：ProductAttribute使用复合主键，需要使用values()然后检查是否存在
            existing_data_list = await ProductAttribute.filter(
                product_id=product_id,
                attribute_id=attribute_id,
                language_id=language_id
            ).values('product_id', 'attribute_id', 'language_id', 'text')
            
            if existing_data_list:
                # 更新现有记录（使用filter().update()）
                await ProductAttribute.filter(
                    product_id=product_id,
                    attribute_id=attribute_id,
                    language_id=language_id
                ).update(text=text)
                logger.info(f"更新商品属性成功: product_id={product_id}, attribute_id={attribute_id}, language_id={language_id}")
            else:
                # 创建新记录（参照PHP：INSERT）
                await ProductAttribute.create(
                    product_id=product_id,
                    attribute_id=attribute_id,
                    language_id=language_id,
                    text=text
                )
                logger.info(f"添加商品属性成功: product_id={product_id}, attribute_id={attribute_id}, language_id={language_id}")
            
        except NotFoundException:
            raise
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"添加商品属性失败: product_id={product_id}, attribute_id={attribute_id}, language_id={language_id}, error={str(e)}")
            raise
    
    async def update_product_attribute(
        self,
        product_id: int,
        attribute_id: int,
        descriptions: List[Dict[str, Any]]
    ) -> None:
        """
        更新商品属性（参照PHP逻辑：先删除再添加）
        
        PHP实现逻辑：
        1. deleteAttributes($product_id, $attribute_id) - 删除该attribute_id的所有语言记录
        2. 循环添加所有语言的描述
        
        Args:
            product_id: 商品ID
            attribute_id: 属性ID
            descriptions: 多语言描述列表，格式：[{"language_id": 1, "text": "..."}, ...]
        """
        try:
            # 验证商品存在
            product = await Product.get_or_none(product_id=product_id)
            if not product:
                raise NotFoundException("商品不存在", {"product_id": f"商品ID {product_id} 不存在"})
            
            # 验证属性存在（更新时如果属性不存在，应该返回404）
            attribute = await Attribute.get_or_none(attribute_id=attribute_id)
            if not attribute:
                raise NotFoundException("属性不存在", {"attribute_id": f"属性ID {attribute_id} 不存在"})
            
            # 验证属性组存在性（参照PHP：属性必须属于某个属性组）
            if attribute.attribute_group_id and attribute.attribute_group_id > 0:
                from app.models.catalog.attribute_group import AttributeGroup
                attribute_group = await AttributeGroup.get_or_none(attribute_group_id=attribute.attribute_group_id)
                if not attribute_group:
                    raise NotFoundException("属性组不存在", {"attribute_group_id": f"属性组ID {attribute.attribute_group_id} 不存在"})
            
            # 验证描述列表
            if not descriptions:
                raise ValidationException("描述列表不能为空", {"descriptions": "至少需要一个语言的描述"})
            
            # 验证重复语言ID（参照PHP：每个语言只能有一个描述）
            language_ids = [desc.get('language_id') for desc in descriptions if desc.get('language_id')]
            if len(language_ids) != len(set(language_ids)):
                raise ValidationException("描述列表中存在重复的语言ID", {"descriptions": "每个语言只能有一个描述"})
            
            # 检查商品属性是否存在（如果不存在，应该返回404）
            # 注意：ProductAttribute使用复合主键，需要使用values()然后取第一个元素
            existing_attr_data_list = await ProductAttribute.filter(
                product_id=product_id,
                attribute_id=attribute_id
            ).values('product_id', 'attribute_id')
            
            existing_attr_data = existing_attr_data_list[0] if existing_attr_data_list else None
            
            if not existing_attr_data:
                raise NotFoundException("商品属性不存在", {"product_id": product_id, "attribute_id": attribute_id})
            
            # 参照PHP实现：先删除该attribute_id的所有记录
            await ProductAttribute.filter(
                product_id=product_id,
                attribute_id=attribute_id
            ).delete()
            
            # 添加所有语言的描述（参照PHP：循环addAttribute）
            for desc in descriptions:
                lang_id = desc.get('language_id')
                text = desc.get('text', '')
                
                if not lang_id:
                    continue
                
                # 验证语言存在
                language = await Language.get_or_none(language_id=lang_id)
                if not language:
                    logger.warning(f"语言不存在，跳过: language_id={lang_id}")
                    continue
                
                # 验证文本长度
                if len(text) > 65535:
                    logger.warning(f"属性文本过长，跳过: language_id={lang_id}, text_length={len(text)}")
                    continue
                
                # 添加记录
                await ProductAttribute.create(
                    product_id=product_id,
                    attribute_id=attribute_id,
                    language_id=lang_id,
                    text=text
                )
            
            logger.info(f"更新商品属性成功: product_id={product_id}, attribute_id={attribute_id}, descriptions_count={len(descriptions)}")
            
        except NotFoundException:
            raise
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"更新商品属性失败: product_id={product_id}, attribute_id={attribute_id}, error={str(e)}")
            raise
    
    async def delete_product_attribute(
        self,
        product_id: int,
        attribute_id: Optional[int] = None
    ) -> None:
        """
        删除商品属性（参照PHP deleteAttributes）
        
        PHP实现：
        - deleteAttributes($product_id) - 删除该商品的所有属性
        - deleteAttributes($product_id, $attribute_id) - 删除该商品的指定属性
        
        Args:
            product_id: 商品ID
            attribute_id: 可选，属性ID。如果提供，只删除该属性；如果不提供，删除该商品的所有属性
        """
        try:
            # 验证商品存在
            product = await Product.get_or_none(product_id=product_id)
            if not product:
                raise NotFoundException("商品不存在", {"product_id": f"商品ID {product_id} 不存在"})
            
            # 构建查询（参照PHP：WHERE product_id = ? [AND attribute_id = ?]）
            query = ProductAttribute.filter(product_id=product_id)
            
            if attribute_id:
                # 验证属性存在
                attribute = await Attribute.get_or_none(attribute_id=attribute_id)
                if not attribute:
                    raise NotFoundException("属性不存在", {"attribute_id": f"属性ID {attribute_id} 不存在"})
                
                query = query.filter(attribute_id=attribute_id)
            
            # 删除记录
            deleted_count = await query.delete()
            
            logger.info(f"删除商品属性成功: product_id={product_id}, attribute_id={attribute_id}, deleted_count={deleted_count}")
            
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"删除商品属性失败: product_id={product_id}, attribute_id={attribute_id}, error={str(e)}")
            raise
    
    async def batch_update_product_attributes(
        self,
        product_id: int,
        attributes: List[ProductAttributeCreate]
    ) -> None:
        """
        批量更新商品属性（参照PHP批量更新逻辑）
        
        PHP实现逻辑（在editProduct中）：
        1. deleteAttributes($product_id) - 删除所有属性
        2. 循环每个product_attribute：
           - deleteAttributes($product_id, $attribute_id) - 删除该attribute_id的所有记录（去重）
           - 循环添加所有语言的描述
        
        Args:
            product_id: 商品ID
            attributes: 商品属性列表
        """
        try:
            # 验证商品存在
            product = await Product.get_or_none(product_id=product_id)
            if not product:
                raise NotFoundException("商品不存在", {"product_id": f"商品ID {product_id} 不存在"})
            
            # 验证重复属性ID（参照PHP：每个属性只能出现一次）
            attribute_ids = [attr.attribute_id for attr in attributes]
            if len(attribute_ids) != len(set(attribute_ids)):
                raise ValidationException("属性列表中存在重复的属性ID", {"attributes": "每个属性只能出现一次"})
            
            # 参照PHP实现：先删除所有属性
            await ProductAttribute.filter(product_id=product_id).delete()
            
            # 循环处理每个属性（参照PHP逻辑）
            for attr_data in attributes:
                attribute_id = attr_data.attribute_id
                
                # 验证属性存在
                attribute = await Attribute.get_or_none(attribute_id=attribute_id)
                if not attribute:
                    logger.warning(f"属性不存在，跳过: attribute_id={attribute_id}")
                    continue
                
                # 验证属性组存在性（参照PHP：属性必须属于某个属性组）
                if attribute.attribute_group_id and attribute.attribute_group_id > 0:
                    from app.models.catalog.attribute_group import AttributeGroup
                    attribute_group = await AttributeGroup.get_or_none(attribute_group_id=attribute.attribute_group_id)
                    if not attribute_group:
                        logger.warning(f"属性组不存在，跳过: attribute_id={attribute_id}, attribute_group_id={attribute.attribute_group_id}")
                        continue
                
                # 验证描述列表不为空
                if not attr_data.descriptions:
                    logger.warning(f"描述列表为空，跳过: attribute_id={attribute_id}")
                    continue
                
                # 验证重复语言ID（参照PHP：每个语言只能有一个描述）
                language_ids = [desc.language_id for desc in attr_data.descriptions]
                if len(language_ids) != len(set(language_ids)):
                    logger.warning(f"描述列表中存在重复的语言ID，跳过: attribute_id={attribute_id}")
                    continue
                
                # 参照PHP：先删除该attribute_id的所有记录（去重，虽然已经全部删除了，但保持逻辑一致）
                await ProductAttribute.filter(
                    product_id=product_id,
                    attribute_id=attribute_id
                ).delete()
                
                # 添加所有语言的描述（参照PHP：循环addAttribute）
                for desc in attr_data.descriptions:
                    lang_id = desc.language_id
                    text = desc.text
                    
                    # 验证语言存在
                    language = await Language.get_or_none(language_id=lang_id)
                    if not language:
                        logger.warning(f"语言不存在，跳过: language_id={lang_id}")
                        continue
                    
                    # 验证文本长度
                    if len(text) > 65535:
                        logger.warning(f"属性文本过长，跳过: language_id={lang_id}, text_length={len(text)}")
                        continue
                    
                    # 添加记录
                    await ProductAttribute.create(
                        product_id=product_id,
                        attribute_id=attribute_id,
                        language_id=lang_id,
                        text=text
                    )
            
            logger.info(f"批量更新商品属性成功: product_id={product_id}, attributes_count={len(attributes)}")
            
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"批量更新商品属性失败: product_id={product_id}, error={str(e)}")
            raise

