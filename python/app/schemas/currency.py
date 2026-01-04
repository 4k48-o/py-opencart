"""
Pydantic schemas for Currency model with validation
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from app.schemas.base import BaseSchema
import re


class CurrencyBase(BaseSchema):
    """Base currency schema with validation"""
    title: Optional[str] = Field(None, max_length=32, description="货币名称（如 'US Dollar', '人民币'）")
    code: Optional[str] = Field(None, max_length=3, description="货币代码（如 'USD', 'CNY'）")
    symbol_left: Optional[str] = Field(None, max_length=12, description="左侧符号（如 '$', '¥'）")
    symbol_right: Optional[str] = Field(None, max_length=12, description="右侧符号")
    decimal_place: Optional[int] = Field(default=2, ge=0, le=8, description="小数位数（0-8，默认2）")
    value: Optional[float] = Field(None, ge=0, description="汇率（正数）")
    status: Optional[int] = Field(default=0, ge=0, le=1, description="状态（0=禁用，1=启用）")
    date_modified: Optional[datetime] = Field(None, description="修改时间")
    
    @field_validator('code')
    @classmethod
    def validate_code(cls, v):
        if v is not None:
            v = v.strip().upper()
            if len(v) != 3:
                raise ValueError("货币代码必须是3个字符（ISO 4217格式）")
            if not re.match(r'^[A-Z]{3}$', v):
                raise ValueError("货币代码必须是3个大写字母（ISO 4217格式）")
        return v
    
    @field_validator('value')
    @classmethod
    def validate_value(cls, v):
        if v is not None and v < 0:
            raise ValueError("汇率必须是正数")
        return v
    
    @field_validator('decimal_place')
    @classmethod
    def validate_decimal_place(cls, v):
        if v is not None and (v < 0 or v > 8):
            raise ValueError("小数位数必须在0-8之间")
        return v
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        if v is not None and v not in [0, 1]:
            raise ValueError("状态必须是0（禁用）或1（启用）")
        return v
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        if v is not None and len(v.strip()) == 0:
            raise ValueError("货币名称不能为空")
        return v.strip() if v else v


class CurrencyCreate(CurrencyBase):
    """Schema for creating a currency"""
    title: str = Field(..., min_length=1, max_length=32, description="货币名称（必填）")
    code: str = Field(..., min_length=3, max_length=3, description="货币代码（必填，ISO 4217格式）")
    symbol_left: Optional[str] = Field(None, max_length=12, description="左侧符号")
    symbol_right: Optional[str] = Field(None, max_length=12, description="右侧符号")
    decimal_place: int = Field(2, ge=0, le=8, description="小数位数（默认2）")
    value: float = Field(..., ge=0, description="汇率（必填，正数）")
    status: int = Field(0, ge=0, le=1, description="状态（默认0=禁用）")
    
    @field_validator('title')
    @classmethod
    def validate_title_required(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("货币名称是必填项且不能为空")
        return v.strip()
    
    @field_validator('code')
    @classmethod
    def validate_code_required(cls, v):
        if not v or len(v.strip()) != 3:
            raise ValueError("货币代码是必填项且必须是3个字符（ISO 4217格式）")
        v = v.strip().upper()
        if not re.match(r'^[A-Z]{3}$', v):
            raise ValueError("货币代码必须是3个大写字母（ISO 4217格式）")
        return v
    
    @field_validator('value')
    @classmethod
    def validate_value_required(cls, v):
        if v is None or v < 0:
            raise ValueError("汇率是必填项且必须是正数")
        return v


class CurrencyUpdate(BaseSchema):
    """Schema for updating a currency"""
    title: Optional[str] = Field(None, min_length=1, max_length=32, description="货币名称")
    code: Optional[str] = Field(None, min_length=3, max_length=3, description="货币代码")
    symbol_left: Optional[str] = Field(None, max_length=12, description="左侧符号")
    symbol_right: Optional[str] = Field(None, max_length=12, description="右侧符号")
    decimal_place: Optional[int] = Field(None, ge=0, le=8, description="小数位数")
    value: Optional[float] = Field(None, ge=0, description="汇率")
    status: Optional[int] = Field(None, ge=0, le=1, description="状态（0=禁用，1=启用）")
    
    @field_validator('code')
    @classmethod
    def validate_code(cls, v):
        if v is not None:
            v = v.strip().upper()
            if len(v) != 3:
                raise ValueError("货币代码必须是3个字符（ISO 4217格式）")
            if not re.match(r'^[A-Z]{3}$', v):
                raise ValueError("货币代码必须是3个大写字母（ISO 4217格式）")
        return v
    
    @field_validator('value')
    @classmethod
    def validate_value(cls, v):
        if v is not None and v < 0:
            raise ValueError("汇率必须是正数")
        return v
    
    @field_validator('decimal_place')
    @classmethod
    def validate_decimal_place(cls, v):
        if v is not None and (v < 0 or v > 8):
            raise ValueError("小数位数必须在0-8之间")
        return v
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        if v is not None and v not in [0, 1]:
            raise ValueError("状态必须是0（禁用）或1（启用）")
        return v
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        if v is not None and len(v.strip()) == 0:
            raise ValueError("货币名称不能为空")
        return v.strip() if v else v


class CurrencyResponse(CurrencyBase):
    """Schema for currency response"""
    currency_id: int = Field(..., description="货币ID", gt=0)
    
    class Config:
        from_attributes = True

