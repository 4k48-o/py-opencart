"""
Tortoise ORM model for order_product table
"""

from tortoise.models import Model
from tortoise import fields
from .order import Order
from ..catalog.product import Product


class OrderProduct(Model):
    """
    OrderProduct model
    
    Represents the order_product table in the OpenCart database.
    
    Attributes:
        order_product_id (int(11)) - Primary key
        order_id (int(11)), nullable
        product_id (int(11)), nullable
        master_id (int(11)), nullable, default: 0
        name (varchar(255)), nullable
        model (varchar(64)), nullable
        quantity (int(4)), nullable, default: 1
        price (decimal(15,4)), nullable, default: 0.0000
        total (decimal(15,4)), nullable, default: 0.0000
        tax (decimal(15,4)), nullable, default: 0.0000
        reward (int(8)), nullable, default: 0
    """

    order_product_id = fields.IntField(pk=True)
    order_id = fields.IntField(null=True)
    product_id = fields.IntField(null=True)
    master_id = fields.IntField(null=True, default=0)
    name = fields.CharField(max_length=255, null=True)
    model = fields.CharField(max_length=64, null=True)
    quantity = fields.IntField(null=True, default=1)
    price = fields.DecimalField(max_digits=15, decimal_places=4, null=True, default='0.0000')
    total = fields.DecimalField(max_digits=15, decimal_places=4, null=True, default='0.0000')
    tax = fields.DecimalField(max_digits=15, decimal_places=4, null=True, default='0.0000')
    reward = fields.IntField(null=True, default=0)

    class Meta:
        table = "oc_order_product"
        indexes = [("order_id",)]

    async def get_order(self):
        """Get related Order"""
        if self.order_id:
            return await Order.get(order_id=self.order_id)
        return None
    async def get_product(self):
        """Get related Product"""
        if self.product_id:
            return await Product.get(product_id=self.product_id)
        return None
    async def get_product(self):
        """Get related Product"""
        if self.master_id:
            return await Product.get(product_id=self.master_id)
        return None
