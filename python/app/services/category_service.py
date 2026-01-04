"""
Category service - 分类服务层
"""
import logging
from typing import List, Optional
from tortoise.exceptions import DoesNotExist, IntegrityError

try:
    from app.models.catalog.category import Category
    from app.models.catalog.category_description import CategoryDescription
    from app.models.catalog.category_path import CategoryPath
    from app.models.catalog.product_to_category import ProductToCategory
    from app.models.localisation.language import Language
except (ImportError, AttributeError):
    import importlib
    category_module = importlib.import_module('app.models.catalog.category')
    Category = category_module.Category
    category_desc_module = importlib.import_module('app.models.catalog.category_description')
    CategoryDescription = category_desc_module.CategoryDescription
    category_path_module = importlib.import_module('app.models.catalog.category_path')
    CategoryPath = category_path_module.CategoryPath
    product_to_category_module = importlib.import_module('app.models.catalog.product_to_category')
    ProductToCategory = product_to_category_module.ProductToCategory
    language_module = importlib.import_module('app.models.localisation.language')
    Language = language_module.Language

from app.schemas.category import (
    CategoryCreate, CategoryUpdate, CategoryResponse,
    CategoryDescriptionResponse, CategoryTreeItem, CategoryPathItem,
    CategoryPathResponse, CategoryMoveRequest
)
from app.services.base_service import BaseService
from app.exceptions import NotFoundException, ConflictException, ValidationException

logger = logging.getLogger(__name__)


class CategoryService(BaseService):
    """分类服务"""
    
    # ==================== 公共方法：查询 ====================
    
    async def get_category(
        self,
        category_id: int,
        language_id: Optional[int] = None,
        include_children: bool = False,
        include_path: bool = False
    ) -> CategoryResponse:
        """
        获取分类详情
        
        Args:
            category_id: 分类ID
            language_id: 语言ID（用于返回对应语言的名称）
            include_children: 是否包含子分类
            include_path: 是否包含路径
            
        Returns:
            CategoryResponse: 分类信息
            
        Raises:
            NotFoundException: 分类不存在
        """
        logger.info(f"开始获取分类详情: category_id={category_id}")
        try:
            category = await Category.get_or_none(category_id=category_id)
            if not category:
                raise NotFoundException("分类", category_id)
            
            response = await self._build_category_response(
                category, language_id, include_children, include_path
            )
            
            logger.info(f"分类详情获取完成: category_id={category_id}")
            return response
        except NotFoundException:
            raise
        except DoesNotExist:
            raise NotFoundException("分类", category_id)
        except Exception as e:
            logger.error(f"获取分类详情失败: category_id={category_id}, error={str(e)}")
            raise
    
    async def list_categories(
        self,
        skip: int = 0,
        limit: int = 20,
        sort: str = "sort_order",
        order: str = "asc",
        filter_name: Optional[str] = None,
        filter_parent_id: Optional[int] = None,
        filter_status: Optional[int] = None,
        language_id: Optional[int] = None
    ) -> List[CategoryResponse]:
        """
        获取分类列表
        
        Args:
            skip: 跳过的记录数
            limit: 返回的记录数
            sort: 排序字段（sort_order）
            order: 排序方向（asc, desc）
            filter_name: 按名称筛选（模糊匹配）
            filter_parent_id: 按父分类ID筛选
            filter_status: 按状态筛选
            language_id: 语言ID（用于返回对应语言的名称）
            
        Returns:
            List[CategoryResponse]: 分类列表
        """
        logger.info(f"开始获取分类列表: skip={skip}, limit={limit}")
        try:
            query = Category.all()
            
            # 父分类筛选
            if filter_parent_id is not None:
                query = query.filter(parent_id=filter_parent_id)
            
            # 状态筛选
            if filter_status is not None:
                query = query.filter(status=filter_status)
            
            # 名称筛选
            if filter_name:
                # 使用 values() 方法避免访问不存在的 'id' 字段（CategoryDescription 使用复合主键）
                desc_data_list = await CategoryDescription.filter(
                    name__icontains=filter_name
                ).values('category_id')
                desc_ids = [desc['category_id'] for desc in desc_data_list if desc.get('category_id')]
                if desc_ids:
                    query = query.filter(category_id__in=desc_ids)
                else:
                    return []
            
            # 排序
            sort_field = sort if sort in ["sort_order"] else "sort_order"
            if order == "desc":
                query = query.order_by(f"-{sort_field}")
            else:
                query = query.order_by(sort_field)
            
            categories = await query.offset(skip).limit(limit)
            
            # 构建响应
            result = []
            for category in categories:
                response = await self._build_category_response(category, language_id)
                result.append(response)
            
            logger.info(f"分类列表获取完成: count={len(result)}")
            return result
        except Exception as e:
            logger.error(f"获取分类列表失败: {str(e)}")
            raise
    
    async def get_category_tree(
        self,
        parent_id: int = 0,
        language_id: Optional[int] = None,
        status_filter: Optional[int] = None,
        depth: Optional[int] = None
    ) -> List[CategoryTreeItem]:
        """
        获取分类树
        
        Args:
            parent_id: 父分类ID（默认0，根分类）
            language_id: 语言ID
            status_filter: 状态筛选（0=禁用，1=启用）
            depth: 最大深度
            
        Returns:
            List[CategoryTreeItem]: 分类树
        """
        logger.info(f"开始获取分类树: parent_id={parent_id}")
        try:
            tree = await self._build_category_tree(
                parent_id, language_id, status_filter, depth, current_depth=0
            )
            logger.info(f"分类树获取完成: parent_id={parent_id}, count={len(tree)}")
            return tree
        except Exception as e:
            logger.error(f"获取分类树失败: {str(e)}")
            raise
    
    # ==================== 私有方法：辅助函数 ====================
    
    async def _get_category_name(
        self,
        category_id: int,
        language_id: Optional[int] = None
    ) -> Optional[str]:
        """
        获取分类名称
        
        Args:
            category_id: 分类ID
            language_id: 语言ID
            
        Returns:
            Optional[str]: 分类名称
        """
        try:
            if language_id:
                desc = await CategoryDescription.get_or_none(
                    category_id=category_id,
                    language_id=language_id
                )
                if desc:
                    return desc.name
            # 如果没有指定语言，返回第一个描述（使用 values() 方法避免访问不存在的 'id' 字段）
            desc_data_list = await CategoryDescription.filter(
                category_id=category_id
            ).limit(1).values('name')
            return desc_data_list[0]['name'] if desc_data_list else None
        except Exception:
            return None
    
    async def _build_category_response(
        self,
        category: Category,
        language_id: Optional[int] = None,
        include_children: bool = False,
        include_path: bool = False
    ) -> CategoryResponse:
        """
        构建分类响应对象
        
        Args:
            category: Category模型实例
            language_id: 语言ID（用于返回对应语言的名称）
            include_children: 是否包含子分类
            include_path: 是否包含路径
            
        Returns:
            CategoryResponse: 分类响应对象
        """
        # 获取所有描述（使用 values() 方法避免访问不存在的 'id' 字段）
        descriptions_data = await CategoryDescription.filter(
            category_id=category.category_id
        ).values('category_id', 'language_id', 'name', 'description', 'meta_title', 'meta_description', 'meta_keyword')
        
        # 构建描述响应
        desc_responses = []
        for desc_data in descriptions_data:
            lang_code = await self.get_language_code(desc_data['language_id'])
            desc_responses.append(CategoryDescriptionResponse(
                language_id=desc_data['language_id'],
                language_code=lang_code,
                name=desc_data['name'] or "",
                description=desc_data['description'],
                meta_title=desc_data['meta_title'],
                meta_description=desc_data['meta_description'],
                meta_keyword=desc_data['meta_keyword']
            ))
        
        # 获取父分类名称
        parent_name = None
        if category.parent_id and category.parent_id > 0:
            parent_name = await self._get_category_name(category.parent_id, language_id)
        
        # 获取子分类数量
        children_count = await Category.filter(parent_id=category.category_id).count()
        
        # 获取商品数量
        product_count = await ProductToCategory.filter(category_id=category.category_id).count()
        
        # 获取当前语言的名称
        name = None
        if language_id:
            desc = await CategoryDescription.get_or_none(
                category_id=category.category_id,
                language_id=language_id
            )
            if desc:
                name = desc.name
        
        # 获取子分类列表
        children = None
        if include_children:
            children_categories = await Category.filter(
                parent_id=category.category_id
            ).order_by('sort_order').all()
            children = []
            for child_cat in children_categories:
                child_name = await self._get_category_name(child_cat.category_id, language_id)
                children.append(CategoryTreeItem(
                    category_id=child_cat.category_id,
                    parent_id=child_cat.parent_id or 0,
                    name=child_name,
                    image=child_cat.image,
                    sort_order=child_cat.sort_order or 0,
                    status=child_cat.status or 0,
                    children=[]
                ))
        
        # 获取路径
        path = None
        if include_path:
            path = await self._build_category_path(category.category_id, language_id)
        
        return CategoryResponse(
            category_id=category.category_id,
            parent_id=category.parent_id or 0,
            image=category.image,
            sort_order=category.sort_order or 0,
            status=category.status or 0,
            descriptions=desc_responses,
            parent_name=parent_name,
            children_count=children_count,
            product_count=product_count,
            name=name,
            children=children,
            path=path
        )
    
    async def _build_category_tree(
        self,
        parent_id: int = 0,
        language_id: Optional[int] = None,
        status_filter: Optional[int] = None,
        depth: Optional[int] = None,
        current_depth: int = 0
    ) -> List[CategoryTreeItem]:
        """
        构建分类树（递归）
        
        Args:
            parent_id: 父分类ID
            language_id: 语言ID
            status_filter: 状态筛选
            depth: 最大深度
            current_depth: 当前深度
            
        Returns:
            List[CategoryTreeItem]: 分类树
        """
        if depth is not None and current_depth >= depth:
            return []
        
        query = Category.filter(parent_id=parent_id)
        if status_filter is not None:
            query = query.filter(status=status_filter)
        
        categories = await query.order_by('sort_order').all()
        
        tree = []
        for category in categories:
            name = await self._get_category_name(category.category_id, language_id)
            children = await self._build_category_tree(
                category.category_id,
                language_id,
                status_filter,
                depth,
                current_depth + 1
            )
            
            tree.append(CategoryTreeItem(
                category_id=category.category_id,
                parent_id=category.parent_id or 0,
                name=name,
                image=category.image,
                sort_order=category.sort_order or 0,
                status=category.status or 0,
                children=children
            ))
        
        return tree
    
    # ==================== 公共方法：CRUD 操作 ====================
    
    async def create_category(
        self,
        data: CategoryCreate
    ) -> CategoryResponse:
        """
        创建分类
        
        Args:
            data: 分类创建数据
            
        Returns:
            CategoryResponse: 创建的分类信息
            
        Raises:
            ValidationException: 验证失败
            ConflictException: 创建失败
        """
        logger.info(f"开始创建分类: parent_id={data.parent_id}")
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
                
                # 验证名称长度和内容（参照PHP实现：name varchar(255)）
                if not desc.name or len(desc.name.strip()) == 0:
                    raise ValidationException(f"语言ID {desc.language_id} 的名称不能为空")
                if len(desc.name) > 255:
                    raise ValidationException(f"语言ID {desc.language_id} 的名称长度不能超过255个字符")
            
            # 验证父分类存在性
            if data.parent_id and data.parent_id > 0:
                parent = await Category.get_or_none(category_id=data.parent_id)
                if not parent:
                    raise ValidationException(f"父分类ID {data.parent_id} 不存在")
            
            # 创建分类
            category = await Category.create(
                parent_id=data.parent_id or 0,
                image=data.image,
                sort_order=data.sort_order or 0,
                status=data.status or 0
            )
            
            # 创建描述
            for desc_data in data.descriptions:
                await CategoryDescription.create(
                    category_id=category.category_id,
                    language_id=desc_data.language_id,
                    name=desc_data.name,
                    description=desc_data.description,
                    meta_title=desc_data.meta_title,
                    meta_description=desc_data.meta_description,
                    meta_keyword=desc_data.meta_keyword
                )
            
            # 更新 CategoryPath 表
            await self._update_category_path(category.category_id)
            
            # 构建响应
            response = await self._build_category_response(category)
            
            logger.info(f"分类创建完成: category_id={category.category_id}")
            return response
        except (ValidationException, ConflictException):
            raise
        except IntegrityError as e:
            logger.error(f"创建分类失败（完整性错误）: {str(e)}")
            raise ConflictException(f"创建分类失败: {str(e)}")
        except Exception as e:
            logger.error(f"创建分类失败: {str(e)}")
            raise
    
    async def update_category(
        self,
        category_id: int,
        data: CategoryCreate
    ) -> CategoryResponse:
        """
        完整更新分类
        
        Args:
            category_id: 分类ID
            data: 分类更新数据
            
        Returns:
            CategoryResponse: 更新后的分类信息
            
        Raises:
            NotFoundException: 分类不存在
            ValidationException: 验证失败
        """
        logger.info(f"开始更新分类: category_id={category_id}")
        try:
            category = await Category.get_or_none(category_id=category_id)
            if not category:
                raise NotFoundException("分类", category_id)
            
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
                
                # 验证名称长度和内容（参照PHP实现：name varchar(255)）
                if not desc.name or len(desc.name.strip()) == 0:
                    raise ValidationException(f"语言ID {desc.language_id} 的名称不能为空")
                if len(desc.name) > 255:
                    raise ValidationException(f"语言ID {desc.language_id} 的名称长度不能超过255个字符")
            
            # 验证父分类存在性和循环引用
            if data.parent_id and data.parent_id > 0:
                if data.parent_id == category_id:
                    raise ValidationException("不能将分类设置为自己的父分类")
                parent = await Category.get_or_none(category_id=data.parent_id)
                if not parent:
                    raise ValidationException(f"父分类ID {data.parent_id} 不存在")
            
            # 更新分类
            old_parent_id = category.parent_id
            category.parent_id = data.parent_id or 0
            category.image = data.image
            category.sort_order = data.sort_order or 0
            category.status = data.status or 0
            await category.save()
            
            # 删除旧描述
            await CategoryDescription.filter(category_id=category_id).delete()
            
            # 创建新描述
            for desc_data in data.descriptions:
                await CategoryDescription.create(
                    category_id=category.category_id,
                    language_id=desc_data.language_id,
                    name=desc_data.name,
                    description=desc_data.description,
                    meta_title=desc_data.meta_title,
                    meta_description=desc_data.meta_description,
                    meta_keyword=desc_data.meta_keyword
                )
            
            # 如果父分类改变，更新 CategoryPath 表
            if old_parent_id != category.parent_id:
                await self._update_category_path(category.category_id)
                await self._repair_categories(category.category_id)
            
            # 构建响应
            response = await self._build_category_response(category)
            
            logger.info(f"分类更新完成: category_id={category_id}")
            return response
        except (NotFoundException, ValidationException):
            raise
        except DoesNotExist:
            raise NotFoundException("分类", category_id)
        except Exception as e:
            logger.error(f"更新分类失败: category_id={category_id}, error={str(e)}")
            raise
    
    async def patch_category(
        self,
        category_id: int,
        data: CategoryUpdate
    ) -> CategoryResponse:
        """
        部分更新分类
        
        Args:
            category_id: 分类ID
            data: 分类更新数据（部分字段）
            
        Returns:
            CategoryResponse: 更新后的分类信息
            
        Raises:
            NotFoundException: 分类不存在
            ValidationException: 验证失败
        """
        logger.info(f"开始部分更新分类: category_id={category_id}")
        try:
            category = await Category.get_or_none(category_id=category_id)
            if not category:
                raise NotFoundException("分类", category_id)
            
            # 更新分类字段
            old_parent_id = category.parent_id
            if data.parent_id is not None:
                if data.parent_id == category_id:
                    raise ValidationException("不能将分类设置为自己的父分类")
                if data.parent_id > 0:
                    parent = await Category.get_or_none(category_id=data.parent_id)
                    if not parent:
                        raise ValidationException(f"父分类ID {data.parent_id} 不存在")
                category.parent_id = data.parent_id
            
            if data.image is not None:
                category.image = data.image
            if data.sort_order is not None:
                category.sort_order = data.sort_order
            if data.status is not None:
                category.status = data.status
            
            await category.save()
            
            # 更新描述（如果提供）
            if data.descriptions is not None:
                # 验证描述数据
                if len(data.descriptions) == 0:
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
                    
                    # 验证名称长度和内容（参照PHP实现：name varchar(255)）
                    if not desc.name or len(desc.name.strip()) == 0:
                        raise ValidationException(f"语言ID {desc.language_id} 的名称不能为空")
                    if len(desc.name) > 255:
                        raise ValidationException(f"语言ID {desc.language_id} 的名称长度不能超过255个字符")
                
                # 删除旧描述
                await CategoryDescription.filter(category_id=category_id).delete()
                
                # 创建新描述
                for desc_data in data.descriptions:
                    await CategoryDescription.create(
                        category_id=category.category_id,
                        language_id=desc_data.language_id,
                        name=desc_data.name,
                        description=desc_data.description,
                        meta_title=desc_data.meta_title,
                        meta_description=desc_data.meta_description,
                        meta_keyword=desc_data.meta_keyword
                    )
            
            # 如果父分类改变，更新 CategoryPath 表
            if old_parent_id != category.parent_id:
                await self._update_category_path(category.category_id)
                await self._repair_categories(category.category_id)
            
            # 构建响应
            response = await self._build_category_response(category)
            
            logger.info(f"分类部分更新完成: category_id={category_id}")
            return response
        except (NotFoundException, ValidationException):
            raise
        except DoesNotExist:
            raise NotFoundException("分类", category_id)
        except Exception as e:
            logger.error(f"部分更新分类失败: category_id={category_id}, error={str(e)}")
            raise
    
    async def update_category_sort(
        self,
        category_id: int,
        sort_order: int
    ) -> CategoryResponse:
        """
        更新分类排序
        
        Args:
            category_id: 分类ID
            sort_order: 新的排序值
            
        Returns:
            CategoryResponse: 更新后的分类信息
            
        Raises:
            NotFoundException: 分类不存在
        """
        logger.info(f"开始更新分类排序: category_id={category_id}, sort_order={sort_order}")
        try:
            category = await Category.get_or_none(category_id=category_id)
            if not category:
                raise NotFoundException("分类", category_id)
            
            category.sort_order = sort_order
            await category.save()
            
            # 构建响应
            response = await self._build_category_response(category)
            
            logger.info(f"分类排序更新完成: category_id={category_id}, sort_order={sort_order}")
            return response
        except NotFoundException:
            raise
        except DoesNotExist:
            raise NotFoundException("分类", category_id)
        except Exception as e:
            logger.error(f"更新分类排序失败: category_id={category_id}, error={str(e)}")
            raise
    
    # ==================== 私有方法：路径管理 ====================
    
    async def _build_category_path(
        self,
        category_id: int,
        language_id: Optional[int] = None
    ) -> List[CategoryPathItem]:
        """
        构建分类路径（向上查找父分类）
        
        Args:
            category_id: 分类ID
            language_id: 语言ID（用于返回名称）
            
        Returns:
            List[CategoryPathItem]: 分类路径列表
        """
        path_items = []
        current_id = category_id
        
        # 通过parent_id向上查找路径
        visited = set()  # 防止循环
        while current_id and current_id not in visited:
            visited.add(current_id)
            category = await Category.get_or_none(category_id=current_id)
            if not category:
                break
            
            name = await self._get_category_name(current_id, language_id)
            path_items.insert(0, CategoryPathItem(
                category_id=current_id,
                name=name or f"Category {current_id}"
            ))
            
            if category.parent_id == 0:
                break
            current_id = category.parent_id
        
        return path_items
    
    async def _update_category_path(
        self,
        category_id: int
    ) -> None:
        """
        更新分类路径（CategoryPath表）
        参照 PHP addCategory() 和 editCategory() 的实现
        
        Args:
            category_id: 分类ID
        """
        category = await Category.get_or_none(category_id=category_id)
        if not category:
            return
        
        # 删除旧路径
        await CategoryPath.filter(category_id=category_id).delete()
        
        # 获取父分类的所有路径（参照 PHP getPaths(parent_id)）
        # 使用 values() 方法避免访问不存在的 'id' 字段（CategoryPath 使用复合主键）
        parent_id = category.parent_id or 0
        parent_paths = []
        if parent_id > 0:
            parent_paths_data = await CategoryPath.filter(
                category_id=parent_id
            ).order_by('level').values('path_id')
            parent_paths = [path['path_id'] for path in parent_paths_data]
        
        # 为每个父路径创建记录（level 递增）
        level = 0
        for path_id in parent_paths:
            await CategoryPath.create(
                category_id=category_id,
                path_id=path_id,
                level=level
            )
            level += 1
        
        # 创建当前分类的路径记录（level 为最后一级）
        await CategoryPath.create(
            category_id=category_id,
            path_id=category_id,
            level=level
        )
    
    async def _repair_categories(
        self,
        parent_id: int = 0
    ) -> None:
        """
        修复子分类路径（递归）
        参照 PHP repairCategories() 的实现
        
        Args:
            parent_id: 父分类ID
        """
        # 获取所有子分类
        children = await Category.filter(parent_id=parent_id).all()
        
        for child in children:
            # 删除子分类的旧路径
            await CategoryPath.filter(category_id=child.category_id).delete()
            
            # 获取父分类的所有路径（使用 values() 方法避免访问不存在的 'id' 字段）
            parent_paths = []
            if parent_id > 0:
                parent_paths_data = await CategoryPath.filter(
                    category_id=parent_id
                ).order_by('level').values('path_id')
                parent_paths = [path['path_id'] for path in parent_paths_data]
            
            # 基于新的父分类路径重建子分类路径
            level = 0
            for path_id in parent_paths:
                await CategoryPath.create(
                    category_id=child.category_id,
                    path_id=path_id,
                    level=level
                )
                level += 1
            
            # 创建子分类自己的路径记录
            await CategoryPath.create(
                category_id=child.category_id,
                path_id=child.category_id,
                level=level
            )
            
            # 递归修复子分类的子分类
            await self._repair_categories(child.category_id)
    
    # ==================== 公共方法：复杂操作 ====================
    
    async def move_category(
        self,
        category_id: int,
        new_parent_id: int
    ) -> CategoryResponse:
        """
        移动分类（改变父分类）
        
        Args:
            category_id: 分类ID
            new_parent_id: 新的父分类ID
            
        Returns:
            CategoryResponse: 更新后的分类信息
            
        Raises:
            NotFoundException: 分类不存在
            ValidationException: 验证失败（循环引用）
        """
        logger.info(f"开始移动分类: category_id={category_id}, new_parent_id={new_parent_id}")
        try:
            category = await Category.get_or_none(category_id=category_id)
            if not category:
                raise NotFoundException("分类", category_id)
            
            # 验证新父分类是否存在
            if new_parent_id > 0:
                new_parent = await Category.get_or_none(category_id=new_parent_id)
                if not new_parent:
                    raise ValidationException(f"父分类ID {new_parent_id} 不存在")
                
                # 检查是否会导致循环（新父分类是否是当前分类的子分类）
                # 通过检查新父分类的路径中是否包含当前分类ID
                parent_path = await self._build_category_path(new_parent_id)
                for path_item in parent_path:
                    if path_item.category_id == category_id:
                        raise ValidationException(
                            "不能将分类移动到自己的子分类下",
                            details={
                                "category_id": category_id,
                                "target_parent_id": new_parent_id
                            }
                        )
            
            # 更新父分类
            old_parent_id = category.parent_id
            category.parent_id = new_parent_id
            await category.save()
            
            # 更新分类路径
            await self._update_category_path(category.category_id)
            
            # 修复子分类路径
            await self._repair_categories(category.category_id)
            
            # 构建响应
            response = await self._build_category_response(category)
            
            logger.info(f"分类移动完成: category_id={category_id}, new_parent_id={new_parent_id}")
            return response
        except (NotFoundException, ValidationException):
            raise
        except DoesNotExist:
            raise NotFoundException("分类", category_id)
        except Exception as e:
            logger.error(f"移动分类失败: category_id={category_id}, error={str(e)}")
            raise
    
    async def delete_category(
        self,
        category_id: int
    ) -> None:
        """
        删除分类
        
        Args:
            category_id: 分类ID
            
        Raises:
            NotFoundException: 分类不存在
            ConflictException: 分类下有子分类或商品，无法删除
        """
        logger.info(f"开始删除分类: category_id={category_id}")
        try:
            category = await Category.get_or_none(category_id=category_id)
            if not category:
                raise NotFoundException("分类", category_id)
            
            # 检查是否有子分类
            children_count = await Category.filter(parent_id=category_id).count()
            if children_count > 0:
                raise ConflictException(
                    "分类下存在子分类，无法删除",
                    details={"children_count": children_count}
                )
            
            # 检查是否有商品
            product_count = await ProductToCategory.filter(category_id=category_id).count()
            if product_count > 0:
                raise ConflictException(
                    "分类下存在商品，无法删除",
                    details={"product_count": product_count}
                )
            
            # 删除 CategoryPath 记录
            await CategoryPath.filter(category_id=category_id).delete()
            await CategoryPath.filter(path_id=category_id).delete()
            
            # 删除分类描述
            await CategoryDescription.filter(category_id=category_id).delete()
            
            # 删除分类
            await category.delete()
            
            logger.info(f"分类删除完成: category_id={category_id}")
        except (NotFoundException, ConflictException):
            raise
        except DoesNotExist:
            raise NotFoundException("分类", category_id)
        except Exception as e:
            logger.error(f"删除分类失败: category_id={category_id}, error={str(e)}")
            raise
    
    async def get_category_path(
        self,
        category_id: int,
        language_id: Optional[int] = None
    ) -> CategoryPathResponse:
        """
        获取分类的完整路径
        
        Args:
            category_id: 分类ID
            language_id: 语言ID
            
        Returns:
            CategoryPathResponse: 分类路径信息
            
        Raises:
            NotFoundException: 分类不存在
        """
        logger.info(f"开始获取分类路径: category_id={category_id}")
        try:
            category = await Category.get_or_none(category_id=category_id)
            if not category:
                raise NotFoundException("分类", category_id)
            
            path = await self._build_category_path(category_id, language_id)
            
            # 构建路径字符串
            path_string = " > ".join([item.name for item in path])
            
            response = CategoryPathResponse(
                category_id=category_id,
                path=path,
                path_string=path_string
            )
            
            logger.info(f"分类路径获取完成: category_id={category_id}")
            return response
        except NotFoundException:
            raise
        except DoesNotExist:
            raise NotFoundException("分类", category_id)
        except Exception as e:
            logger.error(f"获取分类路径失败: category_id={category_id}, error={str(e)}")
            raise

