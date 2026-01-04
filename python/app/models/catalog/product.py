"""
Tortoise ORM model for product table
"""

from tortoise.models import Model
from tortoise import fields
from ..system.stock_status import StockStatus
from .manufacturer import Manufacturer
from ..localisation.tax_class import TaxClass
from ..localisation.weight_class import WeightClass
from ..localisation.length_class import LengthClass


class Product(Model):
    """
    Product model
    
    Represents the product table in the OpenCart database.
    
    Attributes:
        product_id (int(11)) - Primary key
        master_id (int(11)), nullable, default: 0
        model (varchar(64)), nullable
        sku (varchar(64)), nullable
        upc (varchar(12)), nullable
        ean (varchar(14)), nullable
        jan (varchar(13)), nullable
        isbn (varchar(17)), nullable
        mpn (varchar(64)), nullable
        location (varchar(128)), nullable
        variant (text), nullable, default: 
        override (text), nullable, default: 
        quantity (int(4)), nullable, default: 0
        stock_status_id (int(11)), nullable, default: 0
        image (varchar(255)), nullable
        manufacturer_id (int(11)), nullable, default: 0
        shipping (tinyint(1)), nullable, default: 1
        price (decimal(15,4)), nullable, default: 0.0000
        points (int(8)), nullable, default: 0
        tax_class_id (int(11)), nullable, default: 0
        date_available (date), nullable
        weight (decimal(15,8)), nullable, default: 0.00000000
        weight_class_id (int(11)), nullable, default: 0
        length (decimal(15,8)), nullable, default: 0.00000000
        width (decimal(15,8)), nullable, default: 0.00000000
        height (decimal(15,8)), nullable, default: 0.00000000
        length_class_id (int(11)), nullable, default: 0
        subtract (tinyint(1)), nullable, default: 1
        minimum (int(11)), nullable, default: 1
        rating (int(1)), nullable, default: 0
        sort_order (int(11)), nullable, default: 0
        status (tinyint(1)), nullable, default: 0
        date_added (datetime), nullable
        date_modified (datetime), nullable
    """

    product_id = fields.IntField(pk=True)
    master_id = fields.IntField(null=True, default=0)
    model = fields.CharField(max_length=64, null=True)
    sku = fields.CharField(max_length=64, null=True)
    upc = fields.CharField(max_length=12, null=True)
    ean = fields.CharField(max_length=14, null=True)
    jan = fields.CharField(max_length=13, null=True)
    isbn = fields.CharField(max_length=17, null=True)
    mpn = fields.CharField(max_length=64, null=True)
    location = fields.CharField(max_length=128, null=True)
    variant = fields.TextField(null=True, default='')
    override = fields.TextField(null=True, default='')
    quantity = fields.IntField(null=True, default=0)
    stock_status_id = fields.IntField(null=True, default=0)
    image = fields.CharField(max_length=255, null=True)
    manufacturer_id = fields.IntField(null=True, default=0)
    shipping = fields.SmallIntField(null=True, default=1)
    price = fields.DecimalField(max_digits=15, decimal_places=4, null=True, default='0.0000')
    points = fields.IntField(null=True, default=0)
    tax_class_id = fields.IntField(null=True, default=0)
    date_available = fields.DateField(null=True)
    weight = fields.DecimalField(max_digits=15, decimal_places=8, null=True, default='0.00000000')
    weight_class_id = fields.IntField(null=True, default=0)
    length = fields.DecimalField(max_digits=15, decimal_places=8, null=True, default='0.00000000')
    width = fields.DecimalField(max_digits=15, decimal_places=8, null=True, default='0.00000000')
    height = fields.DecimalField(max_digits=15, decimal_places=8, null=True, default='0.00000000')
    length_class_id = fields.IntField(null=True, default=0)
    subtract = fields.SmallIntField(null=True, default=1)
    minimum = fields.IntField(null=True, default=1)
    rating = fields.IntField(null=True, default=0)
    sort_order = fields.IntField(null=True, default=0)
    status = fields.SmallIntField(null=True, default=0)
    date_added = fields.DatetimeField(null=True)
    date_modified = fields.DatetimeField(null=True)

    class Meta:
        table = "oc_product"

    async def get_product(self):
        """Get related Product"""
        if self.master_id:
            # Self-reference: import locally to avoid circular import
            from .product import Product
            return await Product.get(product_id=self.master_id)
        return None
    async def get_stock_status(self):
        """Get related StockStatus"""
        if self.stock_status_id:
            return await StockStatus.get(stock_status_id=self.stock_status_id)
        return None
    async def get_manufacturer(self):
        """Get related Manufacturer"""
        if self.manufacturer_id:
            return await Manufacturer.get(manufacturer_id=self.manufacturer_id)
        return None
    async def get_tax_class(self):
        """Get related TaxClass"""
        if self.tax_class_id:
            return await TaxClass.get(tax_class_id=self.tax_class_id)
        return None
    async def get_weight_class(self):
        """Get related WeightClass"""
        if self.weight_class_id:
            return await WeightClass.get(weight_class_id=self.weight_class_id)
        return None
    async def get_length_class(self):
        """Get related LengthClass"""
        if self.length_class_id:
            return await LengthClass.get(length_class_id=self.length_class_id)
        return None
