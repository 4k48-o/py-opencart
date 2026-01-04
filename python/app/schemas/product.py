"""
Pydantic schemas for Product model
"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import date, datetime
from app.schemas.base import BaseSchema


# ==================== 商品描述Schema ====================

class ProductDescriptionBase(BaseSchema):
    """Base schema for product description"""
    language_id: int = Field(..., ge=1, description="语言ID")
    name: str = Field(..., min_length=1, max_length=255, description="商品名称")
    description: Optional[str] = Field(None, description="商品描述")
    tag: Optional[str] = Field(None, description="商品标签")
    meta_title: Optional[str] = Field(None, max_length=255, description="SEO标题")
    meta_description: Optional[str] = Field(None, max_length=255, description="SEO描述")
    meta_keyword: Optional[str] = Field(None, max_length=255, description="SEO关键词")


class ProductDescriptionCreate(ProductDescriptionBase):
    """Schema for creating product description"""
    pass


class ProductDescriptionResponse(ProductDescriptionBase):
    """Schema for product description response"""
    language_code: Optional[str] = Field(None, description="语言代码")
    
    class Config:
        from_attributes = True


# ==================== 商品属性Schema ====================

class ProductAttributeDescriptionCreate(BaseSchema):
    """Schema for creating product attribute description (多语言属性值)"""
    language_id: int = Field(..., ge=1, description="语言ID")
    text: str = Field(..., max_length=65535, description="属性文本")


class ProductAttributeDescriptionResponse(BaseSchema):
    """Schema for product attribute description response"""
    language_id: int = Field(..., ge=1, description="语言ID")
    language_code: Optional[str] = Field(None, description="语言代码")
    text: str = Field(..., description="属性文本")
    
    class Config:
        from_attributes = True


class ProductAttributeCreate(BaseSchema):
    """Schema for creating product attribute"""
    attribute_id: int = Field(..., ge=1, description="属性ID")
    descriptions: List[ProductAttributeDescriptionCreate] = Field(..., min_length=1, description="多语言属性值数组")


class ProductAttributeResponse(BaseSchema):
    """Schema for product attribute response"""
    attribute_id: int
    attribute: Optional[Dict[str, Any]] = Field(None, description="属性信息")
    text: Optional[str] = Field(None, description="当前语言的属性文本")
    descriptions: List[ProductAttributeDescriptionResponse] = Field(default_factory=list, description="多语言属性值")
    
    class Config:
        from_attributes = True


# ==================== 商品选项值Schema ====================

class ProductOptionValueCreate(BaseSchema):
    """Schema for creating product option value"""
    option_value_id: int = Field(..., ge=1, description="选项值ID")
    quantity: int = Field(default=0, ge=0, description="库存数量")
    subtract: int = Field(default=0, ge=0, le=1, description="是否扣减库存（0=否，1=是）")
    price: Optional[Decimal] = Field(None, description="价格调整")
    price_prefix: Optional[str] = Field(None, max_length=1, description="价格前缀（+/-）")
    points: int = Field(default=0, ge=0, description="积分调整")
    points_prefix: Optional[str] = Field(None, max_length=1, description="积分前缀（+/-）")
    weight: Optional[Decimal] = Field(None, description="重量调整")
    weight_prefix: Optional[str] = Field(None, max_length=1, description="重量前缀（+/-）")
    
    @field_validator('price_prefix', 'points_prefix', 'weight_prefix')
    @classmethod
    def validate_prefix(cls, v):
        if v is not None and v not in ['+', '-']:
            raise ValueError("前缀必须是 '+' 或 '-'")
        return v


class ProductOptionValueResponse(BaseSchema):
    """Schema for product option value response"""
    product_option_value_id: int
    option_value_id: int
    option_value: Optional[Dict[str, Any]] = Field(None, description="选项值信息")
    quantity: int
    subtract: int
    price: Optional[str] = None
    price_prefix: Optional[str] = None
    points: int
    points_prefix: Optional[str] = None
    weight: Optional[str] = None
    weight_prefix: Optional[str] = None
    
    class Config:
        from_attributes = True


# ==================== 商品选项Schema ====================

class ProductOptionCreate(BaseSchema):
    """Schema for creating product option"""
    option_id: int = Field(..., ge=1, description="选项ID")
    value: str = Field(default="", description="选项值（用于text/textarea类型）")
    required: int = Field(default=0, ge=0, le=1, description="是否必填（0=否，1=是）")
    product_option_values: Optional[List[ProductOptionValueCreate]] = Field(None, description="选项值列表（用于select/radio/checkbox类型）")


class ProductOptionResponse(BaseSchema):
    """Schema for product option response"""
    product_option_id: int
    option_id: int
    option: Optional[Dict[str, Any]] = Field(None, description="选项信息")
    value: str
    required: int
    product_option_values: List[ProductOptionValueResponse] = Field(default_factory=list, description="选项值列表")
    
    class Config:
        from_attributes = True


# ==================== 商品图片Schema ====================

class ProductImageCreate(BaseSchema):
    """Schema for creating product image"""
    image: str = Field(..., max_length=255, description="图片路径")
    sort_order: int = Field(default=0, ge=0, description="排序")


class ProductImageResponse(BaseSchema):
    """Schema for product image response"""
    product_image_id: int
    image: str
    sort_order: int
    
    class Config:
        from_attributes = True


# ==================== 商品分类关联Schema ====================

class ProductCategoryResponse(BaseSchema):
    """Schema for product category response"""
    category_id: int
    name: Optional[str] = Field(None, description="分类名称")
    path: Optional[str] = Field(None, description="分类路径")
    
    class Config:
        from_attributes = True


# ==================== 商品主Schema ====================

class ProductBase(BaseSchema):
    """Base schema for product"""
    master_id: Optional[int] = Field(default=0, ge=0, description="主商品ID（0表示主商品，>0表示变体商品）")
    model: str = Field(..., min_length=1, max_length=64, description="商品型号")
    sku: Optional[str] = Field(None, max_length=64, description="商品SKU")
    upc: Optional[str] = Field(None, max_length=12, description="UPC编码")
    ean: Optional[str] = Field(None, max_length=14, description="EAN编码")
    jan: Optional[str] = Field(None, max_length=13, description="JAN编码")
    isbn: Optional[str] = Field(None, max_length=17, description="ISBN编码")
    mpn: Optional[str] = Field(None, max_length=64, description="MPN编码")
    location: Optional[str] = Field(None, max_length=128, description="商品位置")
    quantity: int = Field(default=0, ge=0, description="库存数量")
    minimum: int = Field(default=1, ge=1, description="最小购买量")
    subtract: int = Field(default=1, ge=0, le=1, description="是否扣减库存（0=否，1=是）")
    stock_status_id: int = Field(default=0, ge=0, description="库存状态ID")
    image: Optional[str] = Field(None, max_length=255, description="主图路径")
    manufacturer_id: int = Field(default=0, ge=0, description="制造商ID")
    shipping: int = Field(default=1, ge=0, le=1, description="是否可配送（0=否，1=是）")
    price: Decimal = Field(..., ge=0, description="商品价格")
    points: int = Field(default=0, ge=0, description="积分")
    tax_class_id: int = Field(default=0, ge=0, description="税类ID")
    date_available: Optional[date] = Field(None, description="可用日期")
    weight: Decimal = Field(default=0, ge=0, description="重量")
    weight_class_id: int = Field(default=0, ge=0, description="重量单位ID")
    length: Decimal = Field(default=0, ge=0, description="长度")
    width: Decimal = Field(default=0, ge=0, description="宽度")
    height: Decimal = Field(default=0, ge=0, description="高度")
    length_class_id: int = Field(default=0, ge=0, description="长度单位ID")
    status: int = Field(default=0, ge=0, le=1, description="状态（0=禁用，1=启用）")
    sort_order: int = Field(default=0, ge=0, description="排序")


class ProductCreate(ProductBase):
    """Schema for creating a product"""
    descriptions: List[ProductDescriptionCreate] = Field(..., min_length=1, description="多语言描述数组")
    attributes: Optional[List[ProductAttributeCreate]] = Field(None, description="商品属性数组")
    options: Optional[List[ProductOptionCreate]] = Field(None, description="商品选项数组")
    images: Optional[List[ProductImageCreate]] = Field(None, description="商品图片数组")
    category_ids: Optional[List[int]] = Field(None, description="分类ID数组")
    related_product_ids: Optional[List[int]] = Field(None, description="相关商品ID数组")


class ProductUpdate(ProductBase):
    """Schema for updating a product"""
    master_id: Optional[int] = Field(None, ge=0, description="主商品ID")
    model: Optional[str] = Field(None, min_length=1, max_length=64, description="商品型号")
    price: Optional[Decimal] = Field(None, ge=0, description="商品价格")
    descriptions: Optional[List[ProductDescriptionCreate]] = Field(None, description="多语言描述数组")
    attributes: Optional[List[ProductAttributeCreate]] = Field(None, description="商品属性数组")
    options: Optional[List[ProductOptionCreate]] = Field(None, description="商品选项数组")
    images: Optional[List[ProductImageCreate]] = Field(None, description="商品图片数组")
    category_ids: Optional[List[int]] = Field(None, description="分类ID数组")
    related_product_ids: Optional[List[int]] = Field(None, description="相关商品ID数组")


class ProductResponse(ProductBase):
    """Schema for product response"""
    product_id: int
    descriptions: List[ProductDescriptionResponse] = Field(default_factory=list, description="多语言描述")
    attributes: Optional[List[ProductAttributeResponse]] = Field(None, description="商品属性列表")
    options: Optional[List[ProductOptionResponse]] = Field(None, description="商品选项列表")
    images: Optional[List[ProductImageResponse]] = Field(None, description="商品图片列表")
    categories: Optional[List[ProductCategoryResponse]] = Field(None, description="商品分类列表")
    related_products: Optional[List[Dict[str, Any]]] = Field(None, description="相关商品列表")
    manufacturer: Optional[Dict[str, Any]] = Field(None, description="制造商信息")
    stock_status: Optional[Dict[str, Any]] = Field(None, description="库存状态信息")
    tax_class: Optional[Dict[str, Any]] = Field(None, description="税类信息")
    weight_class: Optional[Dict[str, Any]] = Field(None, description="重量单位信息")
    length_class: Optional[Dict[str, Any]] = Field(None, description="长度单位信息")
    name: Optional[str] = Field(None, description="当前语言的商品名称（用于列表显示）")
    date_added: Optional[datetime] = None
    date_modified: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ==================== 商品列表项Schema ====================

class ProductListItem(BaseSchema):
    """Schema for product list item (简化版，用于列表显示)"""
    product_id: int
    master_id: int
    model: str
    sku: Optional[str] = None
    name: Optional[str] = Field(None, description="商品名称")
    price: str
    quantity: int
    status: int
    image: Optional[str] = None
    manufacturer: Optional[Dict[str, Any]] = None
    categories: Optional[List[Dict[str, Any]]] = None
    date_added: Optional[datetime] = None
    date_modified: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ==================== 商品复制Schema ====================

class ProductCopyRequest(BaseSchema):
    """Schema for copying a product"""
    name_suffix: Optional[str] = Field(None, max_length=50, description="名称后缀（用于区分复制的商品）")
    copy_images: bool = Field(default=True, description="是否复制图片")
    copy_attributes: bool = Field(default=True, description="是否复制属性")
    copy_options: bool = Field(default=True, description="是否复制选项")
    copy_categories: bool = Field(default=True, description="是否复制分类关联")


# ==================== 商品筛选和排序Schema ====================

class ProductFilterParams(BaseSchema):
    """Schema for product filter parameters"""
    name: Optional[str] = Field(None, description="商品名称（模糊匹配）")
    model: Optional[str] = Field(None, description="商品型号（模糊匹配）")
    category_id: Optional[int] = Field(None, ge=1, description="分类ID")
    manufacturer_id: Optional[int] = Field(None, ge=1, description="制造商ID")
    price_from: Optional[Decimal] = Field(None, ge=0, description="最低价格")
    price_to: Optional[Decimal] = Field(None, ge=0, description="最高价格")
    quantity_from: Optional[int] = Field(None, ge=0, description="最低库存")
    quantity_to: Optional[int] = Field(None, ge=0, description="最高库存")
    status: Optional[int] = Field(None, ge=0, le=1, description="状态（0=禁用，1=启用）")
    master_id: Optional[int] = Field(None, ge=0, description="主商品ID（用于查询变体商品）")

