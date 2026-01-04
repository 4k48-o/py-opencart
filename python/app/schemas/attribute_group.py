"""
Pydantic schemas for AttributeGroup model
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from app.schemas.base import BaseSchema


class AttributeGroupDescriptionBase(BaseSchema):
    """Base schema for attribute group description"""
    language_id: int = Field(..., ge=1, description="语言ID")
    name: str = Field(..., min_length=1, max_length=64, description="属性组名称")


class AttributeGroupDescriptionCreate(AttributeGroupDescriptionBase):
    """Schema for creating attribute group description"""
    pass


class AttributeGroupDescriptionResponse(AttributeGroupDescriptionBase):
    """Schema for attribute group description response"""
    language_code: Optional[str] = Field(None, description="语言代码")
    
    class Config:
        from_attributes = True


class AttributeGroupBase(BaseSchema):
    """Base schema for attribute group"""
    sort_order: Optional[int] = Field(default=0, ge=0, description="排序")


class AttributeGroupCreate(AttributeGroupBase):
    """Schema for creating an attribute group"""
    descriptions: List[AttributeGroupDescriptionCreate] = Field(..., min_length=1, description="多语言描述数组")


class AttributeGroupUpdate(AttributeGroupBase):
    """Schema for updating an attribute group"""
    descriptions: Optional[List[AttributeGroupDescriptionCreate]] = Field(None, description="多语言描述数组")


class AttributeGroupResponse(AttributeGroupBase):
    """Schema for attribute group response"""
    attribute_group_id: int
    descriptions: List[AttributeGroupDescriptionResponse] = Field(default_factory=list, description="多语言描述")
    attribute_count: Optional[int] = Field(None, description="属性数量")
    name: Optional[str] = Field(None, description="当前语言的名称（用于列表显示）")
    
    class Config:
        from_attributes = True

