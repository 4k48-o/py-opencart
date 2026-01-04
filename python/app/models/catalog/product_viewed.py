"""
Tortoise ORM model for product_viewed table
"""

from tortoise.models import Model
from tortoise import fields
from .product import Product


class ProductViewed(Model):
    """
    ProductViewed model
    
    Represents the product_viewed table in the OpenCart database.
    
    Attributes:
        product_id (int(11)) - Primary key
        viewed (int(11)), nullable, default: 0
    """

    product_id = fields.IntField(pk=True)
    viewed = fields.IntField(null=True, default=0)

    class Meta:
        table = "oc_product_viewed"

    async def get_product(self):
        """Get related Product"""
        if self.product_id:
            return await Product.get(product_id=self.product_id)
        return None
