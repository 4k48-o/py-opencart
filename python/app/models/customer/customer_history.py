"""
Tortoise ORM model for customer_history table
"""

from tortoise.models import Model
from tortoise import fields


class CustomerHistory(Model):
    """
    CustomerHistory model
    
    Represents the customer_history table in the OpenCart database.
    
    Attributes:
        customer_history_id (int(11)) - Primary key
        customer_id (int(11)), nullable
        comment (text), nullable
        date_added (datetime), nullable
    """

    customer_history_id = fields.IntField(pk=True)
    customer_id = fields.IntField(null=True)
    comment = fields.TextField(null=True)
    date_added = fields.DatetimeField(null=True)

    class Meta:
        table = "oc_customer_history"

