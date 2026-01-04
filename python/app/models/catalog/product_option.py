"""
Tortoise ORM model for product_option table
"""

from tortoise.models import Model
from tortoise import fields
from .product import Product
from .option import Option


class ProductOption(Model):
    """
    ProductOption model
    
    Represents the product_option table in the OpenCart database.
    
    Attributes:
        product_option_id (int(11)) - Primary key
        product_id (int(11)), nullable
        option_id (int(11)), nullable
        value (text), nullable
        required (tinyint(1)), nullable, default: 0
    """

    product_option_id = fields.IntField(pk=True)
    product_id = fields.IntField(null=True)
    option_id = fields.IntField(null=True)
    value = fields.TextField(null=True)
    required = fields.SmallIntField(null=True, default=0)

    class Meta:
        table = "oc_product_option"

    async def get_product(self):
        """Get related Product"""
        if self.product_id:
            return await Product.get(product_id=self.product_id)
        return None
    async def get_option(self):
        """Get related Option"""
        if self.option_id:
            return await Option.get(option_id=self.option_id)
        return None
