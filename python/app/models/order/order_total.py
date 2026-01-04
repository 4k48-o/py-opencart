"""
Tortoise ORM model for order_total table
"""

from tortoise.models import Model
from tortoise import fields
from .order import Order


class OrderTotal(Model):
    """
    OrderTotal model
    
    Represents the order_total table in the OpenCart database.
    
    Attributes:
        order_total_id (int(10)) - Primary key
        order_id (int(11)), nullable
        extension (varchar(255)), nullable
        code (varchar(32)), nullable
        title (varchar(255)), nullable
        value (decimal(15,4)), nullable, default: 0.0000
        sort_order (int(3)), nullable, default: 0
    """

    order_total_id = fields.IntField(pk=True)
    order_id = fields.IntField(null=True)
    extension = fields.CharField(max_length=255, null=True)
    code = fields.CharField(max_length=32, null=True)
    title = fields.CharField(max_length=255, null=True)
    value = fields.DecimalField(max_digits=15, decimal_places=4, null=True, default='0.0000')
    sort_order = fields.IntField(null=True, default=0)

    class Meta:
        table = "oc_order_total"
        indexes = [("order_id",)]

    async def get_order(self):
        """Get related Order"""
        if self.order_id:
            return await Order.get(order_id=self.order_id)
        return None
