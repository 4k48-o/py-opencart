"""
Tortoise ORM model for store table
"""

from tortoise.models import Model
from tortoise import fields


class Store(Model):
    """
    Store model
    
    Represents the store table in the OpenCart database.
    
    Attributes:
        store_id (int(11)) - Primary key
        name (varchar(64)), nullable
        url (varchar(255)), nullable
    """

    store_id = fields.IntField(pk=True)
    name = fields.CharField(max_length=64, null=True)
    url = fields.CharField(max_length=255, null=True)

    class Meta:
        table = "oc_store"

