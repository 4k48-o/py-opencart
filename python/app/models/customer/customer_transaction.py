"""
Tortoise ORM model for customer_transaction table
"""

from tortoise.models import Model
from tortoise import fields
from .customer import Customer
from ..order.order import Order


class CustomerTransaction(Model):
    """
    CustomerTransaction model
    
    Represents the customer_transaction table in the OpenCart database.
    
    Attributes:
        customer_transaction_id (int(11)) - Primary key
        customer_id (int(11)), nullable
        order_id (int(11)), nullable, default: 0
        description (text), nullable
        amount (decimal(15,4)), nullable
        date_added (datetime), nullable
    """

    customer_transaction_id = fields.IntField(pk=True)
    customer_id = fields.IntField(null=True)
    order_id = fields.IntField(null=True, default=0)
    description = fields.TextField(null=True)
    amount = fields.DecimalField(max_digits=15, decimal_places=4, null=True)
    date_added = fields.DatetimeField(null=True)

    class Meta:
        table = "oc_customer_transaction"

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
