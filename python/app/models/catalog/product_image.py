"""
Tortoise ORM model for product_image table
"""

from tortoise.models import Model
from tortoise import fields
from .product import Product


class ProductImage(Model):
    """
    ProductImage model
    
    Represents the product_image table in the OpenCart database.
    
    Attributes:
        product_image_id (int(11)) - Primary key
        product_id (int(11)), nullable
        image (varchar(255)), nullable
        sort_order (int(3)), nullable, default: 0
    """

    product_image_id = fields.IntField(pk=True)
    product_id = fields.IntField(null=True)
    image = fields.CharField(max_length=255, null=True)
    sort_order = fields.IntField(null=True, default=0)

    class Meta:
        table = "oc_product_image"
        indexes = [("product_id",)]

    async def get_product(self):
        """Get related Product"""
        if self.product_id:
            return await Product.get(product_id=self.product_id)
        return None
