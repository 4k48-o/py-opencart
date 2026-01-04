"""
Tortoise ORM model for customer_token table
"""

from tortoise.models import Model
from tortoise import fields
from .customer import Customer


class CustomerToken(Model):
    """
    CustomerToken model
    
    Represents the customer_token table in the OpenCart database.
    
    Attributes:
        customer_token_id (int(11)) - Primary key
        customer_id (int(11)), nullable
        code (text), nullable
        type (varchar(10)), nullable
        date_added (datetime), nullable
    """

    customer_token_id = fields.IntField(pk=True)
    customer_id = fields.IntField(null=True)
    code = fields.TextField(null=True)
    type = fields.CharField(max_length=10, null=True)
    date_added = fields.DatetimeField(null=True)

    class Meta:
        table = "oc_customer_token"

    async def get_customer(self):
        """Get related Customer"""
        if self.customer_id:
            return await Customer.get(customer_id=self.customer_id)
        return None
