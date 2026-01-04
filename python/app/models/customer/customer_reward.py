"""
Tortoise ORM model for customer_reward table
"""

from tortoise.models import Model
from tortoise import fields
from .customer import Customer
from ..order.order import Order


class CustomerReward(Model):
    """
    CustomerReward model
    
    Represents the customer_reward table in the OpenCart database.
    
    Attributes:
        customer_reward_id (int(11)) - Primary key
        customer_id (int(11)), nullable, default: 0
        order_id (int(11)), nullable, default: 0
        description (text), nullable
        points (int(8)), nullable, default: 0
        date_added (datetime), nullable
    """

    customer_reward_id = fields.IntField(pk=True)
    customer_id = fields.IntField(null=True, default=0)
    order_id = fields.IntField(null=True, default=0)
    description = fields.TextField(null=True)
    points = fields.IntField(null=True, default=0)
    date_added = fields.DatetimeField(null=True)

    class Meta:
        table = "oc_customer_reward"

    async def get_customer(self):
        """Get related Customer"""
        if self.customer_id:
            return await Customer.get(customer_id=self.customer_id)
        return None
    async def get_order(self):
        """Get related Order"""
        if self.order_id:
            return await Order.get(order_id=self.order_id)
        return None
