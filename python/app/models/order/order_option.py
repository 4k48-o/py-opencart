"""
Tortoise ORM model for order_option table
"""

from tortoise.models import Model
from tortoise import fields
from .order import Order
from .order_product import OrderProduct
from ..catalog.product_option import ProductOption
from ..catalog.product_option_value import ProductOptionValue


class OrderOption(Model):
    """
    OrderOption model
    
    Represents the order_option table in the OpenCart database.
    
    Attributes:
        order_option_id (int(11)) - Primary key
        order_id (int(11)), nullable
        order_product_id (int(11)), nullable
        product_option_id (int(11)), nullable
        product_option_value_id (int(11)), nullable, default: 0
        name (varchar(255)), nullable
        value (text), nullable
        type (varchar(32)), nullable
    """

    order_option_id = fields.IntField(pk=True)
    order_id = fields.IntField(null=True)
    order_product_id = fields.IntField(null=True)
    product_option_id = fields.IntField(null=True)
    product_option_value_id = fields.IntField(null=True, default=0)
    name = fields.CharField(max_length=255, null=True)
    value = fields.TextField(null=True)
    type = fields.CharField(max_length=32, null=True)

    class Meta:
        table = "oc_order_option"

    async def get_order(self):
        """Get related Order"""
        if self.order_id:
            return await Order.get(order_id=self.order_id)
        return None
    async def get_order_product(self):
        """Get related OrderProduct"""
        if self.order_product_id:
            return await OrderProduct.get(order_product_id=self.order_product_id)
        return None
    async def get_product_option(self):
        """Get related ProductOption"""
        if self.product_option_id:
            return await ProductOption.get(product_option_id=self.product_option_id)
        return None
    async def get_product_option_value(self):
        """Get related ProductOptionValue"""
        if self.product_option_value_id:
            return await ProductOptionValue.get(product_option_value_id=self.product_option_value_id)
        return None
