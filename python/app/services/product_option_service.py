"""
ProductOptionService - 商品选项关联服务

参照PHP实现：
- php/upload/admin/model/catalog/product.php (addOption, deleteOptions, getOptions, addOptionValue)
"""

import logging
from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime
from app.models.catalog.product import Product
from app.models.catalog.product_option import ProductOption
from app.models.catalog.product_option_value import ProductOptionValue
from app.models.catalog.option import Option
from app.models.catalog.option_value import OptionValue
from app.schemas.product import (
    ProductOptionCreate,
    ProductOptionResponse,
    ProductOptionValueCreate,
    ProductOptionValueResponse
)
from app.exceptions import NotFoundException, ValidationException
from app.models.localisation.language import Language

logger = logging.getLogger(__name__)


class ProductOptionService:
    """商品选项关联服务"""
    
    async def list_product_options(
        self,
        product_id: int,
        language_id: Optional[int] = None
    ) -> List[ProductOptionResponse]:
        """
        获取商品选项列表（参照PHP getOptions）
        
        PHP实现逻辑：
        1. 关联product_option, option, option_description表
        2. 按option.sort_order排序
        3. 为每个product_option获取所有product_option_value
        4. 处理date/time/datetime类型的value格式化
        
        Args:
            product_id: 商品ID
            language_id: 可选，指定语言ID（用于获取选项名称）
            
        Returns:
            List[ProductOptionResponse]: 商品选项列表
        """
        try:
            # 验证商品存在
            product = await Product.get_or_none(product_id=product_id)
            if not product:
                raise NotFoundException("商品不存在", {"product_id": f"商品ID {product_id} 不存在"})
            
            # 获取所有商品选项（参照PHP：关联option表）
            product_options = await ProductOption.filter(
                product_id=product_id
            ).all()
            
            if not product_options:
                return []
            
            # 获取所有option_id
            option_ids = list(set([po.option_id for po in product_options if po.option_id]))
            
            # 获取选项信息（用于排序和获取类型）
            options = await Option.filter(option_id__in=option_ids).all()
            option_map = {opt.option_id: opt for opt in options}
            
            # 获取选项描述（用于获取选项名称）
            # 注意：OptionDescription使用复合主键，需要使用values()避免访问不存在的id字段
            from app.models.catalog.option_description import OptionDescription
            if language_id:
                option_descriptions_data = await OptionDescription.filter(
                    option_id__in=option_ids,
                    language_id=language_id
                ).values('option_id', 'language_id', 'name')
            else:
                # 如果没有指定语言，获取第一个语言的描述
                option_descriptions_data = await OptionDescription.filter(
                    option_id__in=option_ids
                ).values('option_id', 'language_id', 'name')
            
            option_desc_map = {}
            for desc_data in option_descriptions_data:
                option_id = desc_data.get('option_id')
                if option_id and option_id not in option_desc_map:
                    option_desc_map[option_id] = desc_data
            
            # 按sort_order排序（参照PHP：ORDER BY o.sort_order ASC）
            sorted_product_options = sorted(
                product_options,
                key=lambda po: option_map.get(po.option_id).sort_order if po.option_id and option_map.get(po.option_id) else 0
            )
            
            result = []
            
            # 为每个product_option获取选项值（参照PHP逻辑）
            for product_option in sorted_product_options:
                option = option_map.get(product_option.option_id) if product_option.option_id else None
                option_desc_data = option_desc_map.get(product_option.option_id) if product_option.option_id else None
                
                # 处理value字段（参照PHP：date/time/datetime格式化）
                value = product_option.value
                if value and option:
                    option_type = option.type
                    if option_type == 'date' and value:
                        try:
                            # 尝试解析日期
                            if isinstance(value, str):
                                dt = datetime.strptime(value, '%Y-%m-%d')
                                value = dt.strftime('%Y-%m-%d')
                        except:
                            pass
                    elif option_type == 'time' and value:
                        try:
                            if isinstance(value, str):
                                dt = datetime.strptime(value, '%H:%M:%S')
                                value = dt.strftime('%H:%M:%S')
                        except:
                            pass
                    elif option_type == 'datetime' and value:
                        try:
                            if isinstance(value, str):
                                dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                                value = dt.strftime('%Y-%m-%d %H:%M:%S')
                        except:
                            pass
                
                # 获取选项值列表（参照PHP：获取product_option_value）
                option_values = []
                if product_option.product_option_id:
                    option_values_data = await ProductOptionValue.filter(
                        product_option_id=product_option.product_option_id
                    ).all()
                    
                    # 获取option_value_id列表用于排序
                    option_value_ids = [ov.option_value_id for ov in option_values_data if ov.option_value_id]
                    
                    # 获取OptionValue信息用于排序
                    if option_value_ids:
                        option_values_info = await OptionValue.filter(
                            option_value_id__in=option_value_ids
                        ).all()
                        option_value_map = {ov.option_value_id: ov for ov in option_values_info}
                        
                        # 按sort_order排序（参照PHP：ORDER BY ov.sort_order ASC）
                        sorted_option_values_data = sorted(
                            option_values_data,
                            key=lambda ov: option_value_map.get(ov.option_value_id).sort_order if ov.option_value_id and option_value_map.get(ov.option_value_id) else 0
                        )
                        
                        # 构建选项值响应
                        for ov in sorted_option_values_data:
                            option_value_info = option_value_map.get(ov.option_value_id) if ov.option_value_id else None
                            
                            option_values.append(ProductOptionValueResponse(
                                product_option_value_id=ov.product_option_value_id,
                                option_value_id=ov.option_value_id or 0,
                                option_value={
                                    "option_value_id": option_value_info.option_value_id if option_value_info else None,
                                    "option_id": option_value_info.option_id if option_value_info else None,
                                    "sort_order": option_value_info.sort_order if option_value_info else None
                                } if option_value_info else None,
                                quantity=ov.quantity or 0,
                                subtract=ov.subtract or 0,
                                price=str(ov.price) if ov.price else None,
                                price_prefix=ov.price_prefix,
                                points=ov.points or 0,
                                points_prefix=ov.points_prefix,
                                weight=str(ov.weight) if ov.weight else None,
                                weight_prefix=ov.weight_prefix
                            ))
                
                # 构建选项响应
                result.append(ProductOptionResponse(
                    product_option_id=product_option.product_option_id,
                    option_id=product_option.option_id,
                    option={
                        "option_id": option.option_id if option else None,
                        "type": option.type if option else None,
                        "sort_order": option.sort_order if option else None,
                        "name": option_desc_data.get('name') if option_desc_data else None
                    } if option else None,
                    value=value,
                    required=product_option.required or 0,
                    product_option_values=option_values
                ))
            
            logger.info(f"获取商品选项列表成功: product_id={product_id}, count={len(result)}")
            return result
            
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"获取商品选项列表失败: product_id={product_id}, error={str(e)}")
            raise
    
    async def add_product_option(
        self,
        product_id: int,
        option_data: ProductOptionCreate
    ) -> int:
        """
        添加商品选项（参照PHP addOption）
        
        PHP实现逻辑：
        1. 插入product_option记录
        2. 如果有product_option_value，循环添加
        
        Args:
            product_id: 商品ID
            option_data: 选项数据
            
        Returns:
            int: 创建的product_option_id
        """
        try:
            # 验证商品存在
            product = await Product.get_or_none(product_id=product_id)
            if not product:
                raise NotFoundException("商品不存在", {"product_id": f"商品ID {product_id} 不存在"})
            
            # 验证选项存在（验证错误应返回ValidationException，而不是NotFoundException）
            option = await Option.get_or_none(option_id=option_data.option_id)
            if not option:
                raise ValidationException("选项不存在", {"option_id": f"选项ID {option_data.option_id} 不存在"})
            
            # 验证选项类型（参照PHP：select/radio/checkbox类型必须有关联的选项值）
            option_type = option.type
            if option_type in ['select', 'radio', 'checkbox']:
                # select/radio/checkbox类型必须提供选项值列表
                if not option_data.product_option_values or len(option_data.product_option_values) == 0:
                    raise ValidationException(
                        f"选项类型 '{option_type}' 必须至少有一个选项值",
                        {"option_type": f"选项类型 '{option_type}' 必须提供选项值列表"}
                    )
            elif option_type in ['text', 'textarea', 'file', 'date', 'time', 'datetime']:
                # text/textarea/file/date/time/datetime类型不需要选项值，使用value字段
                # 注意：这些类型可以没有value（可选），但如果提供了product_option_values则报错
                if option_data.product_option_values and len(option_data.product_option_values) > 0:
                    raise ValidationException(
                        f"选项类型 '{option_type}' 不需要选项值，应使用value字段",
                        {"option_type": f"选项类型 '{option_type}' 不能提供选项值列表"}
                    )
            
            # 验证必填选项（参照PHP：必填选项必须有值或选项值）
            # 注意：必填选项的验证只针对select/radio/checkbox类型，其他类型（text/textarea）的value可以为空
            if option_data.required and option_data.required == 1:
                if option_type in ['select', 'radio', 'checkbox']:
                    if not option_data.product_option_values or len(option_data.product_option_values) == 0:
                        raise ValidationException(
                            "必填选项必须至少有一个选项值",
                            {"required": "必填选项必须提供选项值列表"}
                        )
                # text/textarea类型的必填选项验证在创建时检查value字段
                # 注意：这里不验证text/textarea的value，因为value可以为空（可选字段）
            
            # 创建product_option记录（参照PHP：INSERT INTO product_option）
            product_option = await ProductOption.create(
                product_id=product_id,
                option_id=option_data.option_id,
                value=option_data.value,
                required=option_data.required or 0
            )
            
            product_option_id = product_option.product_option_id
            
            # 如果有选项值，循环添加（参照PHP：循环addOptionValue）
            if option_data.product_option_values:
                for option_value_data in option_data.product_option_values:
                    await self.add_product_option_value(
                        product_id=product_id,
                        product_option_id=product_option_id,
                        option_id=option_data.option_id,
                        option_value_data=option_value_data
                    )
            
            logger.info(f"添加商品选项成功: product_id={product_id}, product_option_id={product_option_id}")
            return product_option_id
            
        except NotFoundException:
            raise
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"添加商品选项失败: product_id={product_id}, error={str(e)}")
            raise
    
    async def delete_product_option(
        self,
        product_id: int,
        product_option_id: Optional[int] = None
    ) -> None:
        """
        删除商品选项（参照PHP deleteOptions）
        
        PHP实现：
        - deleteOptions($product_id) - 删除该商品的所有选项（包括选项值）
        - 如果提供product_option_id，只删除该选项
        
        Args:
            product_id: 商品ID
            product_option_id: 可选，商品选项ID。如果提供，只删除该选项；如果不提供，删除该商品的所有选项
        """
        try:
            # 验证商品存在
            product = await Product.get_or_none(product_id=product_id)
            if not product:
                raise NotFoundException("商品不存在", {"product_id": f"商品ID {product_id} 不存在"})
            
            # 构建查询（参照PHP：WHERE product_id = ? [AND product_option_id = ?]）
            query = ProductOption.filter(product_id=product_id)
            
            if product_option_id:
                # 验证选项存在
                product_option = await ProductOption.get_or_none(
                    product_id=product_id,
                    product_option_id=product_option_id
                )
                if not product_option:
                    raise NotFoundException("商品选项不存在", {"product_option_id": f"商品选项ID {product_option_id} 不存在"})
                
                query = query.filter(product_option_id=product_option_id)
                
                # 删除该选项的所有选项值（参照PHP：deleteOptionValues）
                await ProductOptionValue.filter(
                    product_option_id=product_option_id
                ).delete()
            else:
                # 删除该商品的所有选项值（参照PHP：deleteOptionValues）
                await ProductOptionValue.filter(product_id=product_id).delete()
            
            # 删除选项记录
            deleted_count = await query.delete()
            
            logger.info(f"删除商品选项成功: product_id={product_id}, product_option_id={product_option_id}, deleted_count={deleted_count}")
            
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"删除商品选项失败: product_id={product_id}, product_option_id={product_option_id}, error={str(e)}")
            raise
    
    async def list_product_option_values(
        self,
        product_id: int,
        product_option_id: int
    ) -> List[ProductOptionValueResponse]:
        """
        获取选项值列表
        
        Args:
            product_id: 商品ID
            product_option_id: 商品选项ID
            
        Returns:
            List[ProductOptionValueResponse]: 选项值列表
        """
        try:
            # 验证商品选项存在
            product_option = await ProductOption.get_or_none(
                product_id=product_id,
                product_option_id=product_option_id
            )
            if not product_option:
                raise NotFoundException("商品选项不存在", {"product_option_id": f"商品选项ID {product_option_id} 不存在"})
            
            # 获取选项值列表（参照PHP：按sort_order排序）
            option_values_data = await ProductOptionValue.filter(
                product_option_id=product_option_id
            ).all()
            
            if not option_values_data:
                return []
            
            # 获取option_value_id列表用于排序
            option_value_ids = [ov.option_value_id for ov in option_values_data if ov.option_value_id]
            
            # 获取OptionValue信息用于排序
            option_value_map = {}
            if option_value_ids:
                option_values_info = await OptionValue.filter(
                    option_value_id__in=option_value_ids
                ).all()
                option_value_map = {ov.option_value_id: ov for ov in option_values_info}
            
            # 按sort_order排序（参照PHP：ORDER BY ov.sort_order ASC）
            sorted_option_values_data = sorted(
                option_values_data,
                key=lambda ov: option_value_map.get(ov.option_value_id).sort_order if ov.option_value_id and option_value_map.get(ov.option_value_id) else 0
            )
            
            result = []
            for ov in sorted_option_values_data:
                option_value_info = option_value_map.get(ov.option_value_id) if ov.option_value_id else None
                
                result.append(ProductOptionValueResponse(
                    product_option_value_id=ov.product_option_value_id,
                    option_value_id=ov.option_value_id or 0,
                    option_value={
                        "option_value_id": option_value_info.option_value_id if option_value_info else None,
                        "option_id": option_value_info.option_id if option_value_info else None,
                        "sort_order": option_value_info.sort_order if option_value_info else None
                    } if option_value_info else None,
                    quantity=ov.quantity or 0,
                    subtract=ov.subtract or 0,
                    price=str(ov.price) if ov.price else None,
                    price_prefix=ov.price_prefix,
                    points=ov.points or 0,
                    points_prefix=ov.points_prefix,
                    weight=str(ov.weight) if ov.weight else None,
                    weight_prefix=ov.weight_prefix
                ))
            
            logger.info(f"获取选项值列表成功: product_id={product_id}, product_option_id={product_option_id}, count={len(result)}")
            return result
            
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"获取选项值列表失败: product_id={product_id}, product_option_id={product_option_id}, error={str(e)}")
            raise
    
    async def add_product_option_value(
        self,
        product_id: int,
        product_option_id: int,
        option_id: int,
        option_value_data: ProductOptionValueCreate
    ) -> int:
        """
        添加选项值（参照PHP addOptionValue）
        
        PHP实现：
        INSERT INTO product_option_value SET product_option_id, product_id, option_id, option_value_id, ...
        
        Args:
            product_id: 商品ID
            product_option_id: 商品选项ID
            option_id: 选项ID
            option_value_data: 选项值数据
            
        Returns:
            int: 创建的product_option_value_id
        """
        try:
            # 验证商品选项存在
            product_option = await ProductOption.get_or_none(
                product_id=product_id,
                product_option_id=product_option_id
            )
            if not product_option:
                raise NotFoundException("商品选项不存在", {"product_option_id": f"商品选项ID {product_option_id} 不存在"})
            
            # 验证选项值存在
            option_value = await OptionValue.get_or_none(option_value_id=option_value_data.option_value_id)
            if not option_value:
                raise NotFoundException("选项值不存在", {"option_value_id": f"选项值ID {option_value_data.option_value_id} 不存在"})
            
            # 验证选项值属于该选项
            if option_value.option_id != option_id:
                raise ValidationException("选项值不属于该选项", {"option_value_id": f"选项值ID {option_value_data.option_value_id} 不属于选项ID {option_id}"})
            
            # 验证价格、积分、重量调整（参照PHP：验证前缀和值）
            # 价格调整校验
            if option_value_data.price is not None:
                if option_value_data.price_prefix and option_value_data.price_prefix not in ['+', '-']:
                    raise ValidationException("价格前缀必须是 '+' 或 '-'", {"price_prefix": "价格前缀必须是 '+' 或 '-'"})
                # 价格可以是负数（用于折扣）
            
            # 积分调整校验
            if option_value_data.points is not None and option_value_data.points < 0:
                raise ValidationException("积分调整不能为负数", {"points": "积分调整必须 >= 0"})
            if option_value_data.points_prefix and option_value_data.points_prefix not in ['+', '-']:
                raise ValidationException("积分前缀必须是 '+' 或 '-'", {"points_prefix": "积分前缀必须是 '+' 或 '-'"})
            
            # 重量调整校验
            if option_value_data.weight is not None:
                if option_value_data.weight_prefix and option_value_data.weight_prefix not in ['+', '-']:
                    raise ValidationException("重量前缀必须是 '+' 或 '-'", {"weight_prefix": "重量前缀必须是 '+' 或 '-'"})
                # 重量可以是负数（用于减重）
            
            # 库存数量校验
            if option_value_data.quantity is not None and option_value_data.quantity < 0:
                raise ValidationException("库存数量不能为负数", {"quantity": "库存数量必须 >= 0"})
            
            # 创建选项值记录（参照PHP：INSERT INTO product_option_value）
            product_option_value = await ProductOptionValue.create(
                product_option_id=product_option_id,
                product_id=product_id,
                option_id=option_id,
                option_value_id=option_value_data.option_value_id,
                quantity=option_value_data.quantity or 0,
                subtract=option_value_data.subtract or 0,
                price=option_value_data.price,
                price_prefix=option_value_data.price_prefix,
                points=option_value_data.points or 0,
                points_prefix=option_value_data.points_prefix,
                weight=option_value_data.weight,
                weight_prefix=option_value_data.weight_prefix
            )
            
            logger.info(f"添加选项值成功: product_id={product_id}, product_option_id={product_option_id}, product_option_value_id={product_option_value.product_option_value_id}")
            return product_option_value.product_option_value_id
            
        except NotFoundException:
            raise
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"添加选项值失败: product_id={product_id}, product_option_id={product_option_id}, error={str(e)}")
            raise

