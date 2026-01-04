"""
Pydantic schemas for Category model
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from app.schemas.base import BaseSchema


class CategoryDescriptionBase(BaseSchema):
    """Base schema for category description"""
    language_id: int = Field(..., ge=1, description="语言ID")
    name: str = Field(..., min_length=1, max_length=255, description="分类名称")
    description: Optional[str] = Field(None, description="分类描述")
    meta_title: Optional[str] = Field(None, max_length=255, description="SEO标题")
    meta_description: Optional[str] = Field(None, max_length=255, description="SEO描述")
    meta_keyword: Optional[str] = Field(None, max_length=255, description="SEO关键词")


class CategoryDescriptionCreate(CategoryDescriptionBase):
    """Schema for creating category description"""
    pass


class CategoryDescriptionResponse(CategoryDescriptionBase):
    """Schema for category description response"""
    language_code: Optional[str] = Field(None, description="语言代码")
    
    class Config:
        from_attributes = True


class CategoryBase(BaseSchema):
    """Base schema for category"""
    parent_id: Optional[int] = Field(default=0, ge=0, description="父分类ID（0表示根分类）")
    image: Optional[str] = Field(None, max_length=255, description="分类图片路径")
    sort_order: Optional[int] = Field(default=0, ge=0, description="排序")
    status: Optional[int] = Field(default=0, ge=0, le=1, description="状态（0=禁用，1=启用）")


class CategoryCreate(CategoryBase):
    """Schema for creating a category"""
    descriptions: List[CategoryDescriptionCreate] = Field(..., description="多语言描述数组")


class CategoryUpdate(CategoryBase):
    """Schema for updating a category"""
    parent_id: Optional[int] = Field(None, ge=0, description="父分类ID")
    descriptions: Optional[List[CategoryDescriptionCreate]] = Field(None, description="多语言描述数组")


class CategoryMoveRequest(BaseModel):
    """Schema for moving a category"""
    parent_id: int = Field(..., ge=0, description="新的父分类ID")


class CategoryPathItem(BaseModel):
    """Schema for category path item"""
    category_id: int
    name: str
    
    class Config:
        from_attributes = True


class CategoryPathResponse(BaseModel):
    """Schema for category path response"""
    category_id: int
    path: List[CategoryPathItem] = Field(default_factory=list, description="分类路径")
    path_string: Optional[str] = Field(None, description="路径字符串（如 '电子产品 > 手机 > 智能手机'）")
    
    class Config:
        from_attributes = True


class CategoryTreeItem(BaseModel):
    """Schema for category tree item"""
    category_id: int
    parent_id: int
    name: Optional[str] = None
    image: Optional[str] = None
    sort_order: int = 0
    status: int = 0
    children: List['CategoryTreeItem'] = Field(default_factory=list, description="子分类")
    
    class Config:
        from_attributes = True


# 支持前向引用
CategoryTreeItem.model_rebuild()


class CategoryResponse(CategoryBase):
    """Schema for category response"""
    category_id: int
    descriptions: List[CategoryDescriptionResponse] = Field(default_factory=list, description="多语言描述")
    parent_name: Optional[str] = Field(None, description="父分类名称")
    children_count: Optional[int] = Field(None, description="子分类数量")
    product_count: Optional[int] = Field(None, description="商品数量")
    name: Optional[str] = Field(None, description="当前语言的名称（用于列表显示）")
    children: Optional[List[CategoryTreeItem]] = Field(None, description="子分类列表")
    path: Optional[List[CategoryPathItem]] = Field(None, description="分类路径")
    
    class Config:
        from_attributes = True

