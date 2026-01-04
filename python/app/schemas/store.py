"""
Pydantic schemas for Store model with validation
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from app.schemas.base import BaseSchema, create_url_validator
from app.models.validators import ModelValidators


class StoreBase(BaseSchema):
    """Base store schema with validation"""
    name: Optional[str] = Field(None, max_length=64, description="Store name")
    url: Optional[str] = Field(None, max_length=255, description="Store URL")
    
    # Apply URL validation
    _validate_url = create_url_validator()
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if v is not None and len(v.strip()) == 0:
            raise ValueError("Store name cannot be empty")
        return v.strip() if v else v
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v):
        if v is None:
            return v
        return ModelValidators.validate_url(v)


class StoreCreate(StoreBase):
    """Schema for creating a store with required fields"""
    name: str = Field(..., min_length=1, max_length=64, description="Store name (required)")
    url: str = Field(..., max_length=255, description="Store URL (required)")
    
    @field_validator('name')
    @classmethod
    def validate_name_required(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Store name is required and cannot be empty")
        return v.strip()


class StoreUpdate(BaseSchema):
    """Schema for updating a store"""
    name: Optional[str] = Field(None, min_length=1, max_length=64, description="Store name")
    url: Optional[str] = Field(None, max_length=255, description="Store URL")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if v is not None and len(v.strip()) == 0:
            raise ValueError("Store name cannot be empty")
        return v.strip() if v else v
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v):
        if v is None:
            return v
        return ModelValidators.validate_url(v)


class StoreResponse(StoreBase):
    """Schema for store response"""
    store_id: int = Field(..., description="Store ID", gt=0)
    
    class Config:
        from_attributes = True

