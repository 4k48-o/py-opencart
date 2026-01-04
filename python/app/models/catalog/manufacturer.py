"""
Tortoise ORM model for manufacturer table
"""

from tortoise.models import Model
from tortoise import fields


class Manufacturer(Model):
    """
    Manufacturer model
    
    Represents the manufacturer table in the OpenCart database.
    
    Attributes:
        manufacturer_id (int(11)) - Primary key
        name (varchar(64)), nullable
        image (varchar(255)), nullable
        sort_order (int(3)), nullable, default: 0
    """

    manufacturer_id = fields.IntField(pk=True)
    name = fields.CharField(max_length=64, null=True)
    image = fields.CharField(max_length=255, null=True)
    sort_order = fields.IntField(null=True, default=0)

    class Meta:
        table = "oc_manufacturer"

