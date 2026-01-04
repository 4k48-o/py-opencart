"""
ProductImageService - 商品图片关联服务

参照PHP实现：
- php/upload/admin/model/catalog/product.php (addImage, deleteImages, getImages)
"""

import logging
from typing import List, Optional, Dict
from app.models.catalog.product import Product
from app.models.catalog.product_image import ProductImage
from app.schemas.product import (
    ProductImageCreate,
    ProductImageResponse
)
from app.exceptions import NotFoundException, ValidationException

logger = logging.getLogger(__name__)


class ProductImageService:
    """商品图片关联服务"""
    
    async def list_product_images(
        self,
        product_id: int
    ) -> List[ProductImageResponse]:
        """
        获取商品图片列表（参照PHP getImages）
        
        PHP实现：
        SELECT * FROM product_image WHERE product_id = ? ORDER BY sort_order ASC
        
        Args:
            product_id: 商品ID
            
        Returns:
            List[ProductImageResponse]: 商品图片列表
        """
        try:
            # 验证商品存在
            product = await Product.get_or_none(product_id=product_id)
            if not product:
                raise NotFoundException("商品不存在", {"product_id": f"商品ID {product_id} 不存在"})
            
            # 获取商品图片列表（参照PHP：ORDER BY sort_order ASC）
            product_images = await ProductImage.filter(
                product_id=product_id
            ).order_by('sort_order').all()
            
            result = []
            for img in product_images:
                result.append(ProductImageResponse(
                    product_image_id=img.product_image_id,
                    image=img.image or '',
                    sort_order=img.sort_order or 0
                ))
            
            logger.info(f"获取商品图片列表成功: product_id={product_id}, count={len(result)}")
            return result
            
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"获取商品图片列表失败: product_id={product_id}, error={str(e)}")
            raise
    
    async def add_product_image(
        self,
        product_id: int,
        image_data: ProductImageCreate
    ) -> int:
        """
        添加商品图片（参照PHP addImage）
        
        PHP实现：
        INSERT INTO product_image SET product_id = ?, image = ?, sort_order = ?
        
        注意：这里只是添加图片路径到数据库，实际文件上传应该在Router层处理
        
        Args:
            product_id: 商品ID
            image_data: 图片数据
            
        Returns:
            int: 创建的product_image_id
        """
        try:
            # 验证商品存在
            product = await Product.get_or_none(product_id=product_id)
            if not product:
                raise NotFoundException("商品不存在", {"product_id": f"商品ID {product_id} 不存在"})
            
            # 验证图片路径长度
            if len(image_data.image) > 255:
                raise ValidationException("图片路径过长", {"image": "图片路径长度不能超过255字符"})
            
            # 创建商品图片记录（参照PHP：INSERT INTO product_image）
            product_image = await ProductImage.create(
                product_id=product_id,
                image=image_data.image,
                sort_order=image_data.sort_order or 0
            )
            
            # 主图自动同步到商品image字段（参照PHP：如果商品没有主图，自动设置为第一张图片）
            # PHP实现：在addProduct/editProduct中，如果提供image，更新product.image字段
            if not product.image or product.image == '':
                product.image = image_data.image
                await product.save()
                logger.info(f"自动设置主图: product_id={product_id}, image={image_data.image}")
            
            logger.info(f"添加商品图片成功: product_id={product_id}, product_image_id={product_image.product_image_id}")
            return product_image.product_image_id
            
        except NotFoundException:
            raise
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"添加商品图片失败: product_id={product_id}, error={str(e)}")
            raise
    
    async def delete_product_image(
        self,
        product_id: int,
        product_image_id: Optional[int] = None
    ) -> None:
        """
        删除商品图片（参照PHP deleteImages）
        
        PHP实现：
        - deleteImages($product_id) - 删除该商品的所有图片
        - 如果提供product_image_id，只删除该图片
        
        Args:
            product_id: 商品ID
            product_image_id: 可选，商品图片ID。如果提供，只删除该图片；如果不提供，删除该商品的所有图片
        """
        try:
            # 验证商品存在
            product = await Product.get_or_none(product_id=product_id)
            if not product:
                raise NotFoundException("商品不存在", {"product_id": f"商品ID {product_id} 不存在"})
            
            # 构建查询（参照PHP：WHERE product_id = ? [AND product_image_id = ?]）
            query = ProductImage.filter(product_id=product_id)
            
            if product_image_id:
                # 验证图片存在
                product_image = await ProductImage.get_or_none(
                    product_id=product_id,
                    product_image_id=product_image_id
                )
                if not product_image:
                    raise NotFoundException("商品图片不存在", {"product_image_id": f"商品图片ID {product_image_id} 不存在"})
                
                query = query.filter(product_image_id=product_image_id)
                
                # 如果删除的是主图，需要更新商品image字段（参照PHP逻辑）
                # 检查删除的图片是否是主图
                if product.image and product.image == product_image.image:
                    # 获取剩余的第一张图片作为新主图
                    remaining_images = await ProductImage.filter(
                        product_id=product_id
                    ).exclude(product_image_id=product_image_id).order_by('sort_order').limit(1).all()
                    
                    if remaining_images:
                        # 设置第一张剩余图片为主图
                        product.image = remaining_images[0].image
                        await product.save()
                        logger.info(f"删除主图后自动设置新主图: product_id={product_id}, new_image={remaining_images[0].image}")
                    else:
                        # 没有剩余图片，清空主图
                        product.image = None
                        await product.save()
                        logger.info(f"删除主图后清空主图: product_id={product_id}")
            
            # 删除记录
            deleted_count = await query.delete()
            
            # 如果删除所有图片，清空商品主图（参照PHP逻辑）
            if not product_image_id:
                product.image = None
                await product.save()
                logger.info(f"删除所有图片后清空主图: product_id={product_id}")
            
            logger.info(f"删除商品图片成功: product_id={product_id}, product_image_id={product_image_id}, deleted_count={deleted_count}")
            
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"删除商品图片失败: product_id={product_id}, product_image_id={product_image_id}, error={str(e)}")
            raise
    
    async def set_primary_image(
        self,
        product_id: int,
        product_image_id: int
    ) -> None:
        """
        设置主图（更新Product.image字段）
        
        参照PHP实现：在addProduct/editProduct中，如果提供image，更新product.image字段
        
        Args:
            product_id: 商品ID
            product_image_id: 商品图片ID
        """
        try:
            # 验证商品存在
            product = await Product.get_or_none(product_id=product_id)
            if not product:
                raise NotFoundException("商品不存在", {"product_id": f"商品ID {product_id} 不存在"})
            
            # 验证图片存在
            product_image = await ProductImage.get_or_none(
                product_id=product_id,
                product_image_id=product_image_id
            )
            if not product_image:
                raise NotFoundException("商品图片不存在", {"product_image_id": f"商品图片ID {product_image_id} 不存在"})
            
            # 更新商品主图（参照PHP：UPDATE product SET image = ? WHERE product_id = ?）
            product.image = product_image.image
            await product.save()
            
            logger.info(f"设置主图成功: product_id={product_id}, product_image_id={product_image_id}, image={product_image.image}")
            
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"设置主图失败: product_id={product_id}, product_image_id={product_image_id}, error={str(e)}")
            raise
    
    async def update_image_sort(
        self,
        product_id: int,
        product_image_id: int,
        sort_order: int
    ) -> None:
        """
        更新图片排序（参照PHP：图片按sort_order排序）
        
        PHP实现：getImages按sort_order ASC排序
        
        Args:
            product_id: 商品ID
            product_image_id: 商品图片ID
            sort_order: 排序值
        """
        try:
            # 验证商品存在
            product = await Product.get_or_none(product_id=product_id)
            if not product:
                raise NotFoundException("商品不存在", {"product_id": f"商品ID {product_id} 不存在"})
            
            # 验证图片存在
            product_image = await ProductImage.get_or_none(
                product_id=product_id,
                product_image_id=product_image_id
            )
            if not product_image:
                raise NotFoundException("商品图片不存在", {"product_image_id": f"商品图片ID {product_image_id} 不存在"})
            
            # 验证排序值
            if sort_order < 0:
                raise ValidationException("排序值不能为负数", {"sort_order": "排序值必须 >= 0"})
            
            # 更新排序（参照PHP：sort_order用于排序）
            product_image.sort_order = sort_order
            await product_image.save()
            
            logger.info(f"更新图片排序成功: product_id={product_id}, product_image_id={product_image_id}, sort_order={sort_order}")
            
        except NotFoundException:
            raise
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"更新图片排序失败: product_id={product_id}, product_image_id={product_image_id}, error={str(e)}")
            raise
    
    async def batch_update_image_sort(
        self,
        product_id: int,
        image_sorts: List[Dict[str, int]]
    ) -> None:
        """
        批量更新图片排序（图片排序管理）
        
        Args:
            product_id: 商品ID
            image_sorts: 图片排序列表，格式：[{"product_image_id": 1, "sort_order": 0}, ...]
        """
        try:
            # 验证商品存在
            product = await Product.get_or_none(product_id=product_id)
            if not product:
                raise NotFoundException("商品不存在", {"product_id": f"商品ID {product_id} 不存在"})
            
            # 验证排序列表
            if not image_sorts:
                raise ValidationException("排序列表不能为空", {"image_sorts": "至少需要一个图片的排序信息"})
            
            # 验证重复的product_image_id
            image_ids = [item.get('product_image_id') for item in image_sorts if item.get('product_image_id')]
            if len(image_ids) != len(set(image_ids)):
                raise ValidationException("排序列表中存在重复的图片ID", {"image_sorts": "每个图片ID只能出现一次"})
            
            # 批量更新排序
            for item in image_sorts:
                product_image_id = item.get('product_image_id')
                sort_order = item.get('sort_order', 0)
                
                if not product_image_id:
                    continue
                
                # 验证图片存在
                product_image = await ProductImage.get_or_none(
                    product_id=product_id,
                    product_image_id=product_image_id
                )
                if not product_image:
                    logger.warning(f"图片不存在，跳过: product_image_id={product_image_id}")
                    continue
                
                # 验证排序值
                if sort_order < 0:
                    logger.warning(f"排序值不能为负数，跳过: product_image_id={product_image_id}, sort_order={sort_order}")
                    continue
                
                # 更新排序
                product_image.sort_order = sort_order
                await product_image.save()
            
            logger.info(f"批量更新图片排序成功: product_id={product_id}, count={len(image_sorts)}")
            
        except NotFoundException:
            raise
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"批量更新图片排序失败: product_id={product_id}, error={str(e)}")
            raise

