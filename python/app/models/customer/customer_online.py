"""
Tortoise ORM model for customer_online table
"""

from tortoise.models import Model
from tortoise import fields


class CustomerOnline(Model):
    """
    CustomerOnline model
    
    Represents the customer_online table in the OpenCart database.
    
    Attributes:
        ip (varchar(40)) - Primary key
        customer_id (int(11)), nullable, default: 0
        url (text), nullable
        referer (text), nullable
        date_added (datetime), nullable
    """

    ip = fields.CharField(max_length=40, pk=True)
    customer_id = fields.IntField(null=True, default=0)
    url = fields.TextField(null=True)
    referer = fields.TextField(null=True)
    date_added = fields.DatetimeField(null=True)

    class Meta:
        table = "oc_customer_online"

