"""
Pydantic schemas for Attribute model
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from app.schemas.base import BaseSchema


class AttributeDescriptionBase(BaseSchema):
    """Base schema for attribute description"""
    language_id: int = Field(..., ge=1, description="语言ID")
    name: str = Field(..., min_length=1, max_length=64, description="属性名称")


class AttributeDescriptionCreate(AttributeDescriptionBase):
    """Schema for creating attribute description"""
    pass


class AttributeDescriptionResponse(AttributeDescriptionBase):
    """Schema for attribute description response"""
    language_code: Optional[str] = Field(None, description="语言代码")
    
    class Config:
        from_attributes = True


class AttributeBase(BaseSchema):
    """Base schema for attribute"""
    attribute_group_id: int = Field(..., ge=1, description="属性组ID")
    sort_order: Optional[int] = Field(default=0, ge=0, description="排序")


class AttributeCreate(AttributeBase):
    """Schema for creating an attribute"""
    descriptions: List[AttributeDescriptionCreate] = Field(..., min_length=1, description="多语言描述数组")


class AttributeUpdate(AttributeBase):
    """Schema for updating an attribute"""
    attribute_group_id: Optional[int] = Field(None, ge=1, description="属性组ID")
    descriptions: Optional[List[AttributeDescriptionCreate]] = Field(None, description="多语言描述数组")


class AttributeResponse(AttributeBase):
    """Schema for attribute response"""
    attribute_id: int
    descriptions: List[AttributeDescriptionResponse] = Field(default_factory=list, description="多语言描述")
    attribute_group_name: Optional[str] = Field(None, description="属性组名称")
    name: Optional[str] = Field(None, description="当前语言的名称（用于列表显示）")
    
    class Config:
        from_attributes = True

