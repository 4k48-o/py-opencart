"""
Pydantic schemas for Setting model with validation
"""
import json
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, Any, Dict, List
from app.schemas.base import BaseSchema


class SettingBase(BaseSchema):
    """Base setting schema with validation"""
    store_id: int = Field(default=0, ge=0, description="店铺ID")
    code: Optional[str] = Field(None, max_length=128, description="配置代码（如 'config', 'theme'）")
    key: Optional[str] = Field(None, max_length=128, description="配置键名")
    value: Optional[str] = Field(None, description="配置值（文本）")
    serialized: Optional[int] = Field(default=0, ge=0, le=1, description="是否序列化（0=否，1=是JSON）")
    
    @field_validator('code', 'key')
    @classmethod
    def validate_code_key(cls, v):
        if v is not None and len(v.strip()) == 0:
            raise ValueError("配置代码和键名不能为空")
        return v.strip() if v else v


class SettingCreate(SettingBase):
    """Schema for creating a setting"""
    code: str = Field(..., min_length=1, max_length=128, description="配置代码（必填）")
    key: str = Field(..., min_length=1, max_length=128, description="配置键名（必填）")
    value: str = Field(..., description="配置值（必填）")
    store_id: int = Field(0, ge=0, description="店铺ID（默认0）")
    serialized: int = Field(0, ge=0, le=1, description="是否序列化（默认0）")
    
    @field_validator('code', 'key')
    @classmethod
    def validate_code_key_required(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("配置代码和键名是必填项且不能为空")
        return v.strip()
    
    @model_validator(mode='after')
    def validate_json_value(self):
        """验证值，如果是序列化的，验证JSON格式"""
        # 在 Pydantic v2 中，mode='after' 的验证器是实例方法
        # 此时所有字段已经验证完成，可以访问所有字段的值
        if self.serialized == 1 and self.value:
            try:
                # 验证是否为有效的JSON字符串
                json.loads(self.value)
            except (json.JSONDecodeError, TypeError):
                raise ValueError("当serialized=1时，value必须是有效的JSON格式")
        return self


class SettingUpdate(BaseSchema):
    """Schema for updating a setting"""
    store_id: Optional[int] = Field(None, ge=0, description="店铺ID")
    code: Optional[str] = Field(None, min_length=1, max_length=128, description="配置代码")
    key: Optional[str] = Field(None, min_length=1, max_length=128, description="配置键名")
    value: Optional[str] = Field(None, description="配置值")
    serialized: Optional[int] = Field(None, ge=0, le=1, description="是否序列化")
    
    @field_validator('code', 'key')
    @classmethod
    def validate_code_key(cls, v):
        if v is not None and len(v.strip()) == 0:
            raise ValueError("配置代码和键名不能为空")
        return v.strip() if v else v
    
    @field_validator('value')
    @classmethod
    def validate_value(cls, v, info):
        """验证值，如果是序列化的，验证JSON格式"""
        if v is None:
            return v
        
        # 检查是否需要序列化
        if hasattr(info, 'data') and info.data.get('serialized') == 1:
            try:
                json.loads(v)
            except json.JSONDecodeError:
                raise ValueError("当serialized=1时，value必须是有效的JSON格式")
        
        return v


class SettingResponse(SettingBase):
    """Schema for setting response"""
    setting_id: int = Field(..., description="配置ID", gt=0)
    parsed_value: Optional[Any] = Field(None, description="解析后的值（如果serialized=1，则为JSON对象）")
    
    class Config:
        from_attributes = True
    
    @classmethod
    def model_validate(cls, obj, **kwargs):
        """重写验证方法，自动解析序列化的值"""
        data = super().model_validate(obj, **kwargs)
        
        # 如果serialized=1，解析JSON值
        if data.serialized == 1 and data.value:
            try:
                data.parsed_value = json.loads(data.value)
            except json.JSONDecodeError:
                data.parsed_value = None
        
        return data

