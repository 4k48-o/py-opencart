"""
Tortoise ORM model for customer_ip table
"""

from tortoise.models import Model
from tortoise import fields
from .customer import Customer
from ..system.store import Store


class CustomerIp(Model):
    """
    CustomerIp model
    
    Represents the customer_ip table in the OpenCart database.
    
    Attributes:
        customer_ip_id (int(11)) - Primary key
        customer_id (int(11)), nullable
        store_id (int(11)), nullable, default: 0
        ip (varchar(40)), nullable
        country (varchar(2)), nullable
        date_added (datetime), nullable
    """

    customer_ip_id = fields.IntField(pk=True)
    customer_id = fields.IntField(null=True)
    store_id = fields.IntField(null=True, default=0)
    ip = fields.CharField(max_length=40, null=True)
    country = fields.CharField(max_length=2, null=True)
    date_added = fields.DatetimeField(null=True)

    class Meta:
        table = "oc_customer_ip"
        indexes = [("ip",)]

    async def get_customer(self):
        """Get related Customer"""
        if self.customer_id:
            return await Customer.get(customer_id=self.customer_id)
        return None
    async def get_store(self):
        """Get related Store"""
        if self.store_id:
            return await Store.get(store_id=self.store_id)
        return None
