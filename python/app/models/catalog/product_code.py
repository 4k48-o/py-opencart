"""
Tortoise ORM model for product_code table
"""

from tortoise.models import Model
from tortoise import fields
from .product import Product


class ProductCode(Model):
    """
    ProductCode model
    
    Represents the product_code table in the OpenCart database.
    
    Attributes:
        product_code_id (int(11)) - Primary key
        product_id (int(11)), nullable
        code (varchar(48)), nullable
        value (varchar(255)), nullable
    """

    product_code_id = fields.IntField(pk=True)
    product_id = fields.IntField(null=True)
    code = fields.CharField(max_length=48, null=True)
    value = fields.CharField(max_length=255, null=True)

    class Meta:
        table = "oc_product_code"
        indexes = [("code",)]

    async def get_product(self):
        """Get related Product"""
        if self.product_id:
            return await Product.get(product_id=self.product_id)
        return None
