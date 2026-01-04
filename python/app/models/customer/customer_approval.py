"""
Tortoise ORM model for customer_approval table
"""

from tortoise.models import Model
from tortoise import fields
from .customer import Customer


class CustomerApproval(Model):
    """
    CustomerApproval model
    
    Represents the customer_approval table in the OpenCart database.
    
    Attributes:
        customer_approval_id (int(11)) - Primary key
        customer_id (int(11)), nullable
        type (varchar(9)), nullable
        date_added (datetime), nullable
    """

    customer_approval_id = fields.IntField(pk=True)
    customer_id = fields.IntField(null=True)
    type = fields.CharField(max_length=9, null=True)
    date_added = fields.DatetimeField(null=True)

    class Meta:
        table = "oc_customer_approval"

    async def get_customer(self):
        """Get related Customer"""
        if self.customer_id:
            return await Customer.get(customer_id=self.customer_id)
        return None
