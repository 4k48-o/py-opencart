"""
Pydantic schemas for User management with validation
"""
from pydantic import BaseModel, Field, field_validator, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.schemas.base import BaseSchema, create_email_validator


# ==================== User Schemas ====================

class UserBase(BaseSchema):
    """Base user schema with validation"""
    username: Optional[str] = Field(None, max_length=20, description="用户名")
    user_group_id: Optional[int] = Field(default=0, description="用户组ID")
    firstname: Optional[str] = Field(None, max_length=32, description="名字")
    lastname: Optional[str] = Field(None, max_length=32, description="姓氏")
    email: Optional[EmailStr] = Field(None, max_length=96, description="邮箱")
    image: Optional[str] = Field(None, max_length=255, description="头像")
    status: Optional[int] = Field(default=0, ge=0, le=1, description="状态 (0=禁用, 1=启用)")
    
    _validate_email = create_email_validator()
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if v is not None and len(v.strip()) == 0:
            raise ValueError("用户名不能为空")
        return v.strip() if v else v
    
    @field_validator('firstname', 'lastname')
    @classmethod
    def validate_name(cls, v):
        if v is not None and len(v.strip()) == 0:
            raise ValueError("姓名不能为空")
        return v.strip() if v else v


class UserCreate(UserBase):
    """Schema for creating a user"""
    username: str = Field(..., min_length=1, max_length=20, description="用户名（必填）")
    password: str = Field(..., min_length=6, description="密码（必填，最少6位）")
    user_group_id: int = Field(..., ge=0, description="用户组ID（必填）")
    email: EmailStr = Field(..., max_length=96, description="邮箱（必填）")
    firstname: str = Field(..., min_length=1, max_length=32, description="名字（必填）")
    lastname: str = Field(..., min_length=1, max_length=32, description="姓氏（必填）")
    status: int = Field(1, ge=0, le=1, description="状态 (0=禁用, 1=启用)")
    
    @field_validator('username')
    @classmethod
    def validate_username_required(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("用户名是必填项且不能为空")
        return v.strip()
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError("密码长度至少为6位")
        return v


class UserUpdate(BaseSchema):
    """Schema for updating a user"""
    username: Optional[str] = Field(None, min_length=1, max_length=20, description="用户名")
    password: Optional[str] = Field(None, min_length=6, description="密码（最少6位）")
    user_group_id: Optional[int] = Field(None, ge=0, description="用户组ID")
    firstname: Optional[str] = Field(None, min_length=1, max_length=32, description="名字")
    lastname: Optional[str] = Field(None, min_length=1, max_length=32, description="姓氏")
    email: Optional[EmailStr] = Field(None, max_length=96, description="邮箱")
    image: Optional[str] = Field(None, max_length=255, description="头像")
    status: Optional[int] = Field(None, ge=0, le=1, description="状态 (0=禁用, 1=启用)")
    
    _validate_email = create_email_validator()
    
    @field_validator('username', 'firstname', 'lastname')
    @classmethod
    def validate_name(cls, v):
        if v is not None and len(v.strip()) == 0:
            raise ValueError("字段不能为空")
        return v.strip() if v else v
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if v is not None and len(v) < 6:
            raise ValueError("密码长度至少为6位")
        return v


class UserResponse(UserBase):
    """Schema for user response"""
    user_id: int = Field(..., description="用户ID", gt=0)
    ip: Optional[str] = Field(None, max_length=40, description="IP地址")
    date_added: Optional[datetime] = Field(None, description="创建时间")
    
    class Config:
        from_attributes = True


# ==================== UserGroup Schemas ====================

class UserGroupBase(BaseSchema):
    """Base user group schema"""
    name: Optional[str] = Field(None, max_length=64, description="用户组名称")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if v is not None and len(v.strip()) == 0:
            raise ValueError("用户组名称不能为空")
        return v.strip() if v else v


class UserGroupCreate(UserGroupBase):
    """Schema for creating a user group"""
    name: str = Field(..., min_length=1, max_length=64, description="用户组名称（必填）")
    permission: Optional[Dict[str, List[str]]] = Field(None, description="权限配置（JSON格式）")
    
    @field_validator('name')
    @classmethod
    def validate_name_required(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("用户组名称是必填项且不能为空")
        return v.strip()


class UserGroupUpdate(BaseSchema):
    """Schema for updating a user group"""
    name: Optional[str] = Field(None, min_length=1, max_length=64, description="用户组名称")
    permission: Optional[Dict[str, List[str]]] = Field(None, description="权限配置（JSON格式）")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if v is not None and len(v.strip()) == 0:
            raise ValueError("用户组名称不能为空")
        return v.strip() if v else v


class UserGroupResponse(UserGroupBase):
    """Schema for user group response"""
    user_group_id: int = Field(..., description="用户组ID", gt=0)
    permission: Optional[Dict[str, List[str]]] = Field(None, description="权限配置（JSON格式）")
    
    class Config:
        from_attributes = True


# ==================== UserPermission Schemas ====================

class PermissionUpdate(BaseModel):
    """Schema for updating permissions"""
    resource: str = Field(..., min_length=1, description="资源名称（如：product, order）")
    actions: List[str] = Field(..., min_items=1, description="操作列表（如：['create', 'read', 'update', 'delete']）")
    
    @field_validator('resource', 'actions')
    @classmethod
    def validate_fields(cls, v, info):
        if info.field_name == 'resource' and v:
            if len(v.strip()) == 0:
                raise ValueError("资源名称不能为空")
            return v.strip()
        return v


class PermissionListResponse(BaseModel):
    """Schema for permission list response"""
    resource: str = Field(..., description="资源名称")
    actions: List[str] = Field(..., description="操作列表")


# ==================== UserActivity Schemas ====================

class UserActivityResponse(BaseSchema):
    """Schema for user activity response"""
    user_login_id: int = Field(..., description="登录记录ID", gt=0)
    user_id: Optional[int] = Field(None, description="用户ID")
    ip: Optional[str] = Field(None, max_length=40, description="IP地址")
    user_agent: Optional[str] = Field(None, max_length=255, description="用户代理")
    date_added: Optional[datetime] = Field(None, description="登录时间")
    
    class Config:
        from_attributes = True
