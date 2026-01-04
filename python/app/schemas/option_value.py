"""
Pydantic schemas for OptionValue model
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from app.schemas.base import BaseSchema


class OptionValueDescriptionBase(BaseSchema):
    """Base schema for option value description"""
    language_id: int = Field(..., ge=1, description="语言ID")
    name: str = Field(..., min_length=1, max_length=128, description="选项值名称")


class OptionValueDescriptionCreate(OptionValueDescriptionBase):
    """Schema for creating option value description"""
    pass


class OptionValueDescriptionResponse(OptionValueDescriptionBase):
    """Schema for option value description response"""
    language_code: Optional[str] = Field(None, description="语言代码")
    
    class Config:
        from_attributes = True


class OptionValueBase(BaseSchema):
    """Base schema for option value"""
    option_id: int = Field(..., ge=1, description="选项ID")
    image: Optional[str] = Field(None, max_length=255, description="选项值图片路径")
    sort_order: Optional[int] = Field(default=0, ge=0, description="排序")


class OptionValueCreate(OptionValueBase):
    """Schema for creating an option value"""
    descriptions: List[OptionValueDescriptionCreate] = Field(..., min_length=1, description="多语言描述数组")


class OptionValueUpdate(OptionValueBase):
    """Schema for updating an option value"""
    option_id: Optional[int] = Field(None, ge=1, description="选项ID")
    descriptions: Optional[List[OptionValueDescriptionCreate]] = Field(None, description="多语言描述数组")


class OptionValueResponse(OptionValueBase):
    """Schema for option value response"""
    option_value_id: int
    descriptions: List[OptionValueDescriptionResponse] = Field(default_factory=list, description="多语言描述")
    name: Optional[str] = Field(None, description="当前语言的名称（用于列表显示）")
    
    class Config:
        from_attributes = True


class OptionValueSortUpdate(BaseModel):
    """Schema for batch updating option value sort order"""
    values: List[dict] = Field(..., description="选项值排序数组")
    
    class Config:
        json_schema_extra = {
            "example": {
                "values": [
                    {"option_value_id": 1, "sort_order": 0},
                    {"option_value_id": 2, "sort_order": 1}
                ]
            }
        }

