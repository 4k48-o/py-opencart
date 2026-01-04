"""
Tortoise ORM model for attribute_group table
"""

from tortoise.models import Model
from tortoise import fields


class AttributeGroup(Model):
    """
    AttributeGroup model
    
    Represents the attribute_group table in the OpenCart database.
    
    Attributes:
        attribute_group_id (int(11)) - Primary key
        sort_order (int(3)), nullable, default: 0
    """

    attribute_group_id = fields.IntField(pk=True)
    sort_order = fields.IntField(null=True, default=0)

    class Meta:
        table = "oc_attribute_group"

