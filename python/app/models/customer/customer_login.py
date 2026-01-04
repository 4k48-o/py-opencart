"""
Tortoise ORM model for customer_login table
"""

from tortoise.models import Model
from tortoise import fields


class CustomerLogin(Model):
    """
    CustomerLogin model
    
    Represents the customer_login table in the OpenCart database.
    
    Attributes:
        customer_login_id (int(11)) - Primary key
        email (varchar(96)), nullable
        ip (varchar(40)), nullable
        total (int(4)), nullable, default: 0
        date_added (datetime), nullable
        date_modified (datetime), nullable
    """

    customer_login_id = fields.IntField(pk=True)
    email = fields.CharField(max_length=96, null=True)
    ip = fields.CharField(max_length=40, null=True)
    total = fields.IntField(null=True, default=0)
    date_added = fields.DatetimeField(null=True)
    date_modified = fields.DatetimeField(null=True)

    class Meta:
        table = "oc_customer_login"
        indexes = [("email",), ("ip",)]

