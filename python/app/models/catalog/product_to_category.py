"""
Tortoise ORM model for product_to_category table
"""

from tortoise.models import Model
from tortoise import fields
from .product import Product
from .category import Category


class ProductToCategory(Model):
    """
    ProductToCategory model
    
    Represents the product_to_category table in the OpenCart database.
    
    Attributes:
        product_id (int(11)) - Primary key
        category_id (int(11)) - Primary key
    """

    product_id = fields.IntField(null=True)
    category_id = fields.IntField(null=True)

    class Meta:
        table = "oc_product_to_category"
        indexes = [("category_id",)]
        unique_together = (("product_id", "category_id"),)

    async def get_product(self):
        """Get related Product"""
        if self.product_id:
            return await Product.get(product_id=self.product_id)
        return None
    async def get_category(self):
        """Get related Category"""
        if self.category_id:
            return await Category.get(category_id=self.category_id)
        return None
