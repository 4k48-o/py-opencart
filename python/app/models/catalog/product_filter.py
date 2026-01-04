"""
Tortoise ORM model for product_filter table
"""

from tortoise.models import Model
from tortoise import fields
from .product import Product
from .filter import Filter


class ProductFilter(Model):
    """
    ProductFilter model
    
    Represents the product_filter table in the OpenCart database.
    
    Attributes:
        product_id (int(11)) - Primary key
        filter_id (int(11)) - Primary key
    """

    product_id = fields.IntField(null=True)
    filter_id = fields.IntField(null=True)

    class Meta:
        table = "oc_product_filter"
        unique_together = (("product_id", "filter_id"),)

    async def get_product(self):
        """Get related Product"""
        if self.product_id:
            return await Product.get(product_id=self.product_id)
        return None
    async def get_filter(self):
        """Get related Filter"""
        if self.filter_id:
            return await Filter.get(filter_id=self.filter_id)
        return None
