"""
ProductCategoryService - 商品分类关联服务

参照PHP实现：
- php/upload/admin/model/catalog/product.php (addCategory, deleteCategories, getCategories)
"""

import logging
from typing import List, Optional
from app.models.catalog.product import Product
from app.models.catalog.product_to_category import ProductToCategory
from app.models.catalog.category import Category
from app.schemas.product import ProductCategoryResponse
from app.exceptions import NotFoundException, ValidationException

logger = logging.getLogger(__name__)


class ProductCategoryService:
    """商品分类关联服务"""
    
    async def list_product_categories(
        self,
        product_id: int,
        language_id: Optional[int] = None
    ) -> List[ProductCategoryResponse]:
        """
        获取商品分类列表（参照PHP getCategories）
        
        PHP实现：
        SELECT * FROM product_to_category WHERE product_id = ?
        返回：array<int> category_id列表
        
        Python增强：返回分类信息（包括名称和路径）
        
        Args:
            product_id: 商品ID
            language_id: 可选，指定语言ID（用于获取分类名称）
            
        Returns:
            List[ProductCategoryResponse]: 商品分类列表
        """
        try:
            # 验证商品存在
            product = await Product.get_or_none(product_id=product_id)
            if not product:
                raise NotFoundException("商品不存在", {"product_id": f"商品ID {product_id} 不存在"})
            
            # 获取商品分类关联（参照PHP：SELECT * FROM product_to_category）
            # 注意：ProductToCategory使用复合主键，需要使用values()避免访问不存在的id字段
            category_relations = await ProductToCategory.filter(
                product_id=product_id
            ).values('category_id')
            
            category_ids = [rel['category_id'] for rel in category_relations if rel['category_id']]
            
            if not category_ids:
                return []
            
            # 获取分类信息
            categories = await Category.filter(category_id__in=category_ids).all()
            category_map = {cat.category_id: cat for cat in categories}
            
            # 获取分类描述（用于获取分类名称）
            # 注意：CategoryDescription使用复合主键，需要使用values()避免访问不存在的id字段
            from app.models.catalog.category_description import CategoryDescription
            if language_id:
                category_descriptions_data = await CategoryDescription.filter(
                    category_id__in=category_ids,
                    language_id=language_id
                ).values('category_id', 'language_id', 'name')
            else:
                # 如果没有指定语言，获取第一个语言的描述
                category_descriptions_data = await CategoryDescription.filter(
                    category_id__in=category_ids
                ).values('category_id', 'language_id', 'name')
            
            desc_map = {}
            for desc_data in category_descriptions_data:
                category_id = desc_data.get('category_id')
                if category_id and category_id not in desc_map:
                    desc_map[category_id] = desc_data
            
            # 获取分类路径（用于构建分类路径字符串）
            from app.models.catalog.category_path import CategoryPath
            category_paths = await CategoryPath.filter(
                category_id__in=category_ids
            ).order_by('level').values('category_id', 'path_id', 'level')
            
            # 构建分类路径映射
            path_map = {}
            for path_data in category_paths:
                cat_id = path_data['category_id']
                path_id = path_data['path_id']
                if cat_id not in path_map:
                    path_map[cat_id] = []
                path_map[cat_id].append(path_id)
            
            result = []
            for category_id in category_ids:
                category = category_map.get(category_id)
                desc_data = desc_map.get(category_id)
                
                # 构建分类路径字符串（参照PHP：getPath方法）
                path_ids = path_map.get(category_id, [])
                path_str = '_'.join(str(pid) for pid in path_ids) if path_ids else str(category_id)
                
                result.append(ProductCategoryResponse(
                    category_id=category_id,
                    name=desc_data.get('name') if desc_data else None,
                    path=path_str
                ))
            
            logger.info(f"获取商品分类列表成功: product_id={product_id}, count={len(result)}")
            return result
            
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"获取商品分类列表失败: product_id={product_id}, error={str(e)}")
            raise
    
    async def add_product_category(
        self,
        product_id: int,
        category_id: int
    ) -> None:
        """
        添加商品分类（参照PHP addCategory）
        
        PHP实现：
        INSERT INTO product_to_category SET product_id = ?, category_id = ?
        
        Args:
            product_id: 商品ID
            category_id: 分类ID
        """
        try:
            # 验证商品存在
            product = await Product.get_or_none(product_id=product_id)
            if not product:
                raise NotFoundException("商品不存在", {"product_id": f"商品ID {product_id} 不存在"})
            
            # 校验逻辑：分类存在性校验
            category = await Category.get_or_none(category_id=category_id)
            if not category:
                raise NotFoundException("分类不存在", {"category_id": f"分类ID {category_id} 不存在"})
            
            # 校验逻辑：重复分类校验（参照PHP：避免重复）
            # 注意：ProductToCategory使用复合主键，需要使用values()然后检查是否存在
            existing_data_list = await ProductToCategory.filter(
                product_id=product_id,
                category_id=category_id
            ).values('product_id', 'category_id')
            
            existing = existing_data_list[0] if existing_data_list else None
            if existing:
                raise ValidationException("商品分类关联已存在", {"category_id": f"商品已关联分类ID {category_id}"})
            
            # 创建商品分类关联（参照PHP：INSERT INTO product_to_category）
            await ProductToCategory.create(
                product_id=product_id,
                category_id=category_id
            )
            
            logger.info(f"添加商品分类成功: product_id={product_id}, category_id={category_id}")
            
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"添加商品分类失败: product_id={product_id}, category_id={category_id}, error={str(e)}")
            raise
    
    async def delete_product_category(
        self,
        product_id: int,
        category_id: Optional[int] = None
    ) -> None:
        """
        删除商品分类（参照PHP deleteCategories）
        
        PHP实现：
        - deleteCategories($product_id) - 删除该商品的所有分类
        - 如果提供category_id，只删除该分类
        
        Args:
            product_id: 商品ID
            category_id: 可选，分类ID。如果提供，只删除该分类；如果不提供，删除该商品的所有分类
        """
        try:
            # 验证商品存在
            product = await Product.get_or_none(product_id=product_id)
            if not product:
                raise NotFoundException("商品不存在", {"product_id": f"商品ID {product_id} 不存在"})
            
            # 构建查询（参照PHP：WHERE product_id = ? [AND category_id = ?]）
            query = ProductToCategory.filter(product_id=product_id)
            
            if category_id:
                # 验证分类存在
                category = await Category.get_or_none(category_id=category_id)
                if not category:
                    raise NotFoundException("分类不存在", {"category_id": f"分类ID {category_id} 不存在"})
                
                query = query.filter(category_id=category_id)
            
            # 删除记录
            deleted_count = await query.delete()
            
            logger.info(f"删除商品分类成功: product_id={product_id}, category_id={category_id}, deleted_count={deleted_count}")
            
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"删除商品分类失败: product_id={product_id}, category_id={category_id}, error={str(e)}")
            raise
    
    async def batch_update_product_categories(
        self,
        product_id: int,
        category_ids: List[int]
    ) -> None:
        """
        批量更新商品分类（参照PHP批量更新逻辑）
        
        PHP实现逻辑（在editProduct中）：
        1. deleteCategories($product_id) - 删除所有分类
        2. 循环添加新的分类
        
        Args:
            product_id: 商品ID
            category_ids: 分类ID列表
        """
        try:
            # 验证商品存在
            product = await Product.get_or_none(product_id=product_id)
            if not product:
                raise NotFoundException("商品不存在", {"product_id": f"商品ID {product_id} 不存在"})
            
            # 校验逻辑：重复分类校验（参照PHP：每个分类只能出现一次）
            if len(category_ids) != len(set(category_ids)):
                raise ValidationException("分类ID列表中存在重复的分类ID", {"category_ids": "每个分类ID只能出现一次"})
            
            # 校验逻辑：分类存在性校验（批量验证所有分类是否存在）
            invalid_category_ids = []
            for category_id in category_ids:
                category = await Category.get_or_none(category_id=category_id)
                if not category:
                    invalid_category_ids.append(category_id)
            
            if invalid_category_ids:
                raise NotFoundException(
                    "部分分类不存在",
                    {"category_ids": f"分类ID {', '.join(map(str, invalid_category_ids))} 不存在"}
                )
            
            # 参照PHP实现：先删除所有分类
            await ProductToCategory.filter(product_id=product_id).delete()
            
            # 循环添加新的分类（参照PHP：循环addCategory）
            # 所有分类已验证存在，直接创建
            for category_id in category_ids:
                await ProductToCategory.create(
                    product_id=product_id,
                    category_id=category_id
                )
            
            logger.info(f"批量更新商品分类成功: product_id={product_id}, category_ids_count={len(category_ids)}")
            
        except NotFoundException:
            raise
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"批量更新商品分类失败: product_id={product_id}, error={str(e)}")
            raise

