"""
Tortoise ORM model for order_history table
"""

from tortoise.models import Model
from tortoise import fields
from .order import Order
from .order_status import OrderStatus


class OrderHistory(Model):
    """
    OrderHistory model
    
    Represents the order_history table in the OpenCart database.
    
    Attributes:
        order_history_id (int(11)) - Primary key
        order_id (int(11)), nullable
        order_status_id (int(11)), nullable, default: 0
        notify (tinyint(1)), nullable, default: 0
        comment (text), nullable
        date_added (datetime), nullable
    """

    order_history_id = fields.IntField(pk=True)
    order_id = fields.IntField(null=True)
    order_status_id = fields.IntField(null=True, default=0)
    notify = fields.SmallIntField(null=True, default=0)
    comment = fields.TextField(null=True)
    date_added = fields.DatetimeField(null=True)

    class Meta:
        table = "oc_order_history"

    async def get_order(self):
        """Get related Order"""
        if self.order_id:
            return await Order.get(order_id=self.order_id)
        return None
    async def get_order_status(self):
        """Get related OrderStatus"""
        if self.order_status_id:
            return await OrderStatus.get(order_status_id=self.order_status_id)
        return None
