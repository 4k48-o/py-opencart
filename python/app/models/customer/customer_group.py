"""
Tortoise ORM model for customer_group table
"""

from tortoise.models import Model
from tortoise import fields


class CustomerGroup(Model):
    """
    CustomerGroup model
    
    Represents the customer_group table in the OpenCart database.
    
    Attributes:
        customer_group_id (int(11)) - Primary key
        approval (int(1)), nullable, default: 0
        sort_order (int(3)), nullable, default: 0
    """

    customer_group_id = fields.IntField(pk=True)
    approval = fields.IntField(null=True, default=0)
    sort_order = fields.IntField(null=True, default=0)

    class Meta:
        table = "oc_customer_group"

