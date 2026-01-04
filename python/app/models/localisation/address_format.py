"""
Tortoise ORM model for address_format table
"""

from tortoise.models import Model
from tortoise import fields


class AddressFormat(Model):
    """
    AddressFormat model
    
    Represents the address_format table in the OpenCart database.
    
    Attributes:
        address_format_id (int(11)) - Primary key
        name (varchar(128)), nullable
        address_format (text), nullable
    """

    address_format_id = fields.IntField(pk=True)
    name = fields.CharField(max_length=128, null=True)
    address_format = fields.TextField(null=True)

    class Meta:
        table = "oc_address_format"

