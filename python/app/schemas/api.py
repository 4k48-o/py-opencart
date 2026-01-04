"""
API Key management schemas
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ApiKeyBase(BaseModel):
    """Base API key schema"""
    username: Optional[str] = Field(None, max_length=64, description="API用户名")
    status: Optional[int] = Field(default=0, ge=0, le=1, description="状态 (0=禁用, 1=启用)")
    
    class Config:
        from_attributes = True


class ApiKeyCreate(ApiKeyBase):
    """Schema for creating an API key"""
    username: str = Field(..., min_length=1, max_length=64, description="API用户名（必填）")
    status: int = Field(1, ge=0, le=1, description="状态 (0=禁用, 1=启用)")


class ApiKeyUpdate(BaseModel):
    """Schema for updating an API key"""
    username: Optional[str] = Field(None, min_length=1, max_length=64, description="API用户名")
    status: Optional[int] = Field(None, ge=0, le=1, description="状态 (0=禁用, 1=启用)")


class ApiKeyResponse(ApiKeyBase):
    """Schema for API key response"""
    api_id: int = Field(..., description="API ID", gt=0)
    key: Optional[str] = Field(None, description="API密钥（仅创建时返回）")
    date_added: Optional[datetime] = Field(None, description="创建时间")
    date_modified: Optional[datetime] = Field(None, description="修改时间")
    
    class Config:
        from_attributes = True


class ApiKeyCreateResponse(BaseModel):
    """Schema for API key creation response"""
    api_id: int = Field(..., description="API ID")
    username: str = Field(..., description="API用户名")
    key: str = Field(..., description="API密钥（仅显示一次）")
    status: int = Field(..., description="状态")
    message: str = Field(default="请妥善保管API密钥，系统不会再次显示", description="提示信息")

