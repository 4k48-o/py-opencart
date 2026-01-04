"""
Tortoise ORM model for customer_authorize table
"""

from tortoise.models import Model
from tortoise import fields
from .customer import Customer


class CustomerAuthorize(Model):
    """
    CustomerAuthorize model
    
    Represents the customer_authorize table in the OpenCart database.
    
    Attributes:
        customer_authorize_id (int(11)) - Primary key
        customer_id (int(11)), nullable
        token (varchar(96)), nullable
        total (int(1)), nullable, default: 0
        ip (varchar(40)), nullable
        user_agent (varchar(255)), nullable
        status (tinyint(1)), nullable, default: 0
        date_added (datetime), nullable
        date_expire (datetime), nullable
    """

    customer_authorize_id = fields.IntField(pk=True)
    customer_id = fields.IntField(null=True)
    token = fields.CharField(max_length=96, null=True)
    total = fields.IntField(null=True, default=0)
    ip = fields.CharField(max_length=40, null=True)
    user_agent = fields.CharField(max_length=255, null=True)
    status = fields.SmallIntField(null=True, default=0)
    date_added = fields.DatetimeField(null=True)
    date_expire = fields.DatetimeField(null=True)

    class Meta:
        table = "oc_customer_authorize"

    async def get_customer(self):
        """Get related Customer"""
        if self.customer_id:
            return await Customer.get(customer_id=self.customer_id)
        return None
