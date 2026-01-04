"""
Tortoise ORM model for product_related table
"""

from tortoise.models import Model
from tortoise import fields
from .product import Product


class ProductRelated(Model):
    """
    ProductRelated model
    
    Represents the product_related table in the OpenCart database.
    
    Attributes:
        product_id (int(11)) - Primary key
        related_id (int(11)) - Primary key
    """

    product_id = fields.IntField(null=True)
    related_id = fields.IntField(null=True)

    class Meta:
        table = "oc_product_related"
        unique_together = (("product_id", "related_id"),)

    async def get_product(self):
        """Get related Product"""
        if self.product_id:
            return await Product.get(product_id=self.product_id)
        return None
    async def get_related_product(self):
        """Get related Product (the related product)"""
        if self.related_id:
            return await Product.get(product_id=self.related_id)
        return None
