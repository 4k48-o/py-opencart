"""
Tortoise ORM model for attribute table
"""

from tortoise.models import Model
from tortoise import fields
from .attribute_group import AttributeGroup


class Attribute(Model):
    """
    Attribute model
    
    Represents the attribute table in the OpenCart database.
    
    Attributes:
        attribute_id (int(11)) - Primary key
        attribute_group_id (int(11)), nullable, default: 0
        sort_order (int(3)), nullable, default: 0
    """

    attribute_id = fields.IntField(pk=True)
    attribute_group_id = fields.IntField(null=True, default=0)
    sort_order = fields.IntField(null=True, default=0)

    class Meta:
        table = "oc_attribute"

    async def get_attribute_group(self):
        """Get related AttributeGroup"""
        if self.attribute_group_id:
            return await AttributeGroup.get(attribute_group_id=self.attribute_group_id)
        return None
