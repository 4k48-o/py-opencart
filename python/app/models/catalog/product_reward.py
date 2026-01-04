"""
Tortoise ORM model for product_reward table
"""

from tortoise.models import Model
from tortoise import fields
from .product import Product
from ..customer.customer_group import CustomerGroup


class ProductReward(Model):
    """
    ProductReward model
    
    Represents the product_reward table in the OpenCart database.
    
    Attributes:
        product_reward_id (int(11)) - Primary key
        product_id (int(11)), nullable, default: 0
        customer_group_id (int(11)), nullable, default: 0
        points (int(8)), nullable, default: 0
    """

    product_reward_id = fields.IntField(pk=True)
    product_id = fields.IntField(null=True, default=0)
    customer_group_id = fields.IntField(null=True, default=0)
    points = fields.IntField(null=True, default=0)

    class Meta:
        table = "oc_product_reward"

    async def get_product(self):
        """Get related Product"""
        if self.product_id:
            return await Product.get(product_id=self.product_id)
        return None
    async def get_customer_group(self):
        """Get related CustomerGroup"""
        if self.customer_group_id:
            return await CustomerGroup.get(customer_group_id=self.customer_group_id)
        return None
