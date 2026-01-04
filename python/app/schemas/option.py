"""
Pydantic schemas for Option model
"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from app.schemas.base import BaseSchema


class OptionDescriptionBase(BaseSchema):
    """Base schema for option description"""
    language_id: int = Field(..., ge=1, description="语言ID")
    name: str = Field(..., min_length=1, max_length=128, description="选项名称")


class OptionDescriptionCreate(OptionDescriptionBase):
    """Schema for creating option description"""
    pass


class OptionDescriptionResponse(OptionDescriptionBase):
    """Schema for option description response"""
    language_code: Optional[str] = Field(None, description="语言代码")
    
    class Config:
        from_attributes = True


class OptionBase(BaseSchema):
    """Base schema for option"""
    type: str = Field(..., description="选项类型")
    validation: Optional[str] = Field(None, max_length=255, description="验证规则")
    sort_order: Optional[int] = Field(default=0, ge=0, description="排序")
    
    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        valid_types = ['select', 'radio', 'checkbox', 'text', 'textarea', 'file', 'date', 'datetime', 'time', 'image']
        if v not in valid_types:
            raise ValueError(f"选项类型必须是以下之一: {', '.join(valid_types)}")
        return v


class OptionCreate(OptionBase):
    """Schema for creating an option"""
    descriptions: List[OptionDescriptionCreate] = Field(..., min_length=1, description="多语言描述数组")


class OptionUpdate(OptionBase):
    """Schema for updating an option"""
    type: Optional[str] = Field(None, description="选项类型")
    descriptions: Optional[List[OptionDescriptionCreate]] = Field(None, description="多语言描述数组")


class OptionResponse(OptionBase):
    """Schema for option response"""
    option_id: int
    descriptions: List[OptionDescriptionResponse] = Field(default_factory=list, description="多语言描述")
    value_count: Optional[int] = Field(None, description="选项值数量")
    name: Optional[str] = Field(None, description="当前语言的名称（用于列表显示）")
    
    class Config:
        from_attributes = True

