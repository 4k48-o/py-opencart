"""
Pydantic schemas for Manufacturer model
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from app.schemas.base import BaseSchema


class ManufacturerBase(BaseSchema):
    """Base schema for manufacturer"""
    name: str = Field(..., min_length=1, max_length=64, description="制造商名称")
    image: Optional[str] = Field(None, max_length=255, description="制造商图片路径")
    sort_order: Optional[int] = Field(default=0, ge=0, description="排序顺序")


class ManufacturerCreate(ManufacturerBase):
    """Schema for creating a manufacturer"""
    manufacturer_store: Optional[List[int]] = Field(default=[0], description="店铺ID数组，默认[0]（默认店铺）")
    manufacturer_seo_url: Optional[Dict[str, Dict[int, str]]] = Field(None, description="SEO URL对象，格式：{store_id: {language_id: keyword}}")
    manufacturer_layout: Optional[Dict[str, int]] = Field(None, description="布局对象，格式：{store_id: layout_id}")


class ManufacturerUpdate(ManufacturerBase):
    """Schema for updating a manufacturer"""
    name: Optional[str] = Field(None, min_length=1, max_length=64, description="制造商名称")
    manufacturer_store: Optional[List[int]] = Field(None, description="店铺ID数组")
    manufacturer_seo_url: Optional[Dict[str, Dict[int, str]]] = Field(None, description="SEO URL对象")
    manufacturer_layout: Optional[Dict[str, int]] = Field(None, description="布局对象")


class ManufacturerPatch(BaseModel):
    """Schema for patching a manufacturer (partial update)"""
    name: Optional[str] = Field(None, min_length=1, max_length=64, description="制造商名称")
    image: Optional[str] = Field(None, max_length=255, description="制造商图片路径")
    sort_order: Optional[int] = Field(None, ge=0, description="排序顺序")
    manufacturer_store: Optional[List[int]] = Field(None, description="店铺ID数组")
    manufacturer_seo_url: Optional[Dict[str, Dict[int, str]]] = Field(None, description="SEO URL对象")
    manufacturer_layout: Optional[Dict[str, int]] = Field(None, description="布局对象")


class StoreInfo(BaseModel):
    """Schema for store information"""
    store_id: int
    name: Optional[str] = None
    
    class Config:
        from_attributes = True


class LanguageInfo(BaseModel):
    """Schema for language information"""
    language_id: int
    name: Optional[str] = None
    code: Optional[str] = None
    
    class Config:
        from_attributes = True


class SeoUrlItem(BaseModel):
    """Schema for SEO URL item"""
    seo_url_id: int
    store_id: int
    language_id: int
    keyword: str
    store: Optional[StoreInfo] = None
    language: Optional[LanguageInfo] = None
    
    class Config:
        from_attributes = True


class LayoutItem(BaseModel):
    """Schema for layout item"""
    store_id: int
    layout_id: int
    store: Optional[StoreInfo] = None
    layout: Optional[Dict] = None
    
    class Config:
        from_attributes = True


class ManufacturerStoreItem(BaseModel):
    """Schema for manufacturer store item"""
    store_id: int
    store: Optional[StoreInfo] = None
    
    class Config:
        from_attributes = True


class ManufacturerResponse(ManufacturerBase):
    """Schema for manufacturer response"""
    manufacturer_id: int
    stores: Optional[List[int]] = Field(None, description="店铺ID数组")
    layouts: Optional[Dict[str, int]] = Field(None, description="布局对象，格式：{store_id: layout_id}")
    seo_urls: Optional[List[SeoUrlItem]] = Field(None, description="SEO URL列表")
    product_count: Optional[int] = Field(None, description="关联商品数量")
    
    class Config:
        from_attributes = True


class ManufacturerListItem(BaseModel):
    """Schema for manufacturer list item"""
    manufacturer_id: int
    name: str
    image: Optional[str] = None
    sort_order: int = 0
    product_count: Optional[int] = None
    
    class Config:
        from_attributes = True


class ManufacturerAutocompleteItem(BaseModel):
    """Schema for manufacturer autocomplete item"""
    manufacturer_id: int
    name: str
    
    class Config:
        from_attributes = True


class ManufacturerBatchDeleteRequest(BaseModel):
    """Schema for batch delete request"""
    ids: List[int] = Field(..., min_length=1, description="制造商ID数组")


class ManufacturerBatchDeleteResponse(BaseModel):
    """Schema for batch delete response"""
    deleted: int = Field(..., description="成功删除的数量")
    failed: int = Field(..., description="失败的数量")
    results: List[Dict] = Field(..., description="详细结果")


class ManufacturerStoreUpdateRequest(BaseModel):
    """Schema for manufacturer store update request"""
    store_ids: List[int] = Field(..., min_length=1, description="店铺ID数组")


class ManufacturerStoreUpdateResponse(BaseModel):
    """Schema for manufacturer store update response"""
    added: int = Field(..., description="新增的数量")
    removed: int = Field(..., description="删除的数量")
    total: int = Field(..., description="总数量")


class ManufacturerSeoUrlUpdateRequest(BaseModel):
    """Schema for manufacturer SEO URL update request"""
    seo_urls: Dict[str, Dict[int, str]] = Field(..., description="SEO URL对象，格式：{store_id: {language_id: keyword}}")


class ManufacturerSeoUrlUpdateResponse(BaseModel):
    """Schema for manufacturer SEO URL update response"""
    updated: int = Field(..., description="更新的数量")
    total: int = Field(..., description="总数量")


class ManufacturerLayoutUpdateRequest(BaseModel):
    """Schema for manufacturer layout update request"""
    layouts: Dict[str, int] = Field(..., description="布局对象，格式：{store_id: layout_id}")


class ManufacturerLayoutUpdateResponse(BaseModel):
    """Schema for manufacturer layout update response"""
    updated: int = Field(..., description="更新的数量")
    total: int = Field(..., description="总数量")


class ProductListItem(BaseModel):
    """Schema for product list item"""
    product_id: int
    name: Optional[str] = None
    image: Optional[str] = None
    price: Optional[str] = None
    status: int = 0
    sort_order: int = 0
    
    class Config:
        from_attributes = True

