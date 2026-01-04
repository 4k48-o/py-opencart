"""
Tortoise ORM model for customer_activity table
"""

from tortoise.models import Model
from tortoise import fields
from .customer import Customer


class CustomerActivity(Model):
    """
    CustomerActivity model
    
    Represents the customer_activity table in the OpenCart database.
    
    Attributes:
        customer_activity_id (int(11)) - Primary key
        customer_id (int(11)), nullable
        key (varchar(64)), nullable
        data (text), nullable
        ip (varchar(40)), nullable
        date_added (datetime), nullable
    """

    customer_activity_id = fields.IntField(pk=True)
    customer_id = fields.IntField(null=True)
    key = fields.CharField(max_length=64, null=True)
    data = fields.TextField(null=True)
    ip = fields.CharField(max_length=40, null=True)
    date_added = fields.DatetimeField(null=True)

    class Meta:
        table = "oc_customer_activity"

    async def get_customer(self):
        """Get related Customer"""
        if self.customer_id:
            return await Customer.get(customer_id=self.customer_id)
        return None
