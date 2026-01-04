"""
Tortoise ORM model for product_report table
"""

from tortoise.models import Model
from tortoise import fields
from .product import Product
from ..system.store import Store


class ProductReport(Model):
    """
    ProductReport model
    
    Represents the product_report table in the OpenCart database.
    
    Attributes:
        product_report_id (int(11)) - Primary key
        product_id (int(11)), nullable
        store_id (int(11)), nullable, default: 0
        ip (varchar(40)), nullable
        country (varchar(2)), nullable
        date_added (datetime), nullable
    """

    product_report_id = fields.IntField(pk=True)
    product_id = fields.IntField(null=True)
    store_id = fields.IntField(null=True, default=0)
    ip = fields.CharField(max_length=40, null=True)
    country = fields.CharField(max_length=2, null=True)
    date_added = fields.DatetimeField(null=True)

    class Meta:
        table = "oc_product_report"

    async def get_product(self):
        """Get related Product"""
        if self.product_id:
            return await Product.get(product_id=self.product_id)
        return None
    async def get_store(self):
        """Get related Store"""
        if self.store_id:
            return await Store.get(store_id=self.store_id)
        return None
