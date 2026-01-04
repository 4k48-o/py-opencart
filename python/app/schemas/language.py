"""
Pydantic schemas for Language model with validation
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from app.schemas.base import BaseSchema
import re


class LanguageBase(BaseSchema):
    """Base language schema with validation"""
    name: Optional[str] = Field(None, max_length=32, description="语言名称（如 'English', '中文'）")
    code: Optional[str] = Field(None, max_length=5, description="语言代码（如 'en', 'zh-CN'）")
    locale: Optional[str] = Field(None, max_length=255, description="区域设置")
    extension: Optional[str] = Field(None, max_length=255, description="扩展名")
    sort_order: Optional[int] = Field(default=0, ge=0, description="排序")
    status: Optional[int] = Field(default=0, ge=0, le=1, description="状态（0=禁用，1=启用）")
    
    @field_validator('code')
    @classmethod
    def validate_code(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) < 2 or len(v) > 5:
                raise ValueError("语言代码长度必须在2-5个字符之间")
            # 验证格式：字母、数字、连字符、下划线
            if not re.match(r'^[a-zA-Z0-9_-]+$', v):
                raise ValueError("语言代码只能包含字母、数字、连字符和下划线")
        return v
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        if v is not None and v not in [0, 1]:
            raise ValueError("状态必须是0（禁用）或1（启用）")
        return v
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if v is not None and len(v.strip()) == 0:
            raise ValueError("语言名称不能为空")
        return v.strip() if v else v


class LanguageCreate(LanguageBase):
    """Schema for creating a language"""
    name: str = Field(..., min_length=1, max_length=32, description="语言名称（必填）")
    code: str = Field(..., min_length=2, max_length=5, description="语言代码（必填）")
    locale: Optional[str] = Field(None, max_length=255, description="区域设置")
    extension: Optional[str] = Field(None, max_length=255, description="扩展名")
    sort_order: int = Field(0, ge=0, description="排序（默认0）")
    status: int = Field(0, ge=0, le=1, description="状态（默认0=禁用）")
    
    @field_validator('name')
    @classmethod
    def validate_name_required(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("语言名称是必填项且不能为空")
        return v.strip()
    
    @field_validator('code')
    @classmethod
    def validate_code_required(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError("语言代码是必填项且长度至少2个字符")
        v = v.strip()
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError("语言代码只能包含字母、数字、连字符和下划线")
        return v


class LanguageUpdate(BaseSchema):
    """Schema for updating a language"""
    name: Optional[str] = Field(None, min_length=1, max_length=32, description="语言名称")
    code: Optional[str] = Field(None, min_length=2, max_length=5, description="语言代码")
    locale: Optional[str] = Field(None, max_length=255, description="区域设置")
    extension: Optional[str] = Field(None, max_length=255, description="扩展名")
    sort_order: Optional[int] = Field(None, ge=0, description="排序")
    status: Optional[int] = Field(None, ge=0, le=1, description="状态（0=禁用，1=启用）")
    
    @field_validator('code')
    @classmethod
    def validate_code(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) < 2 or len(v) > 5:
                raise ValueError("语言代码长度必须在2-5个字符之间")
            if not re.match(r'^[a-zA-Z0-9_-]+$', v):
                raise ValueError("语言代码只能包含字母、数字、连字符和下划线")
        return v
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        if v is not None and v not in [0, 1]:
            raise ValueError("状态必须是0（禁用）或1（启用）")
        return v
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if v is not None and len(v.strip()) == 0:
            raise ValueError("语言名称不能为空")
        return v.strip() if v else v


class LanguageResponse(LanguageBase):
    """Schema for language response"""
    language_id: int = Field(..., description="语言ID", gt=0)
    
    class Config:
        from_attributes = True

