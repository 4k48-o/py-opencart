"""
Tortoise ORM model for attribute_group_description table
"""

from tortoise.models import Model
from tortoise import fields
from .attribute_group import AttributeGroup
from ..localisation.language import Language


class AttributeGroupDescription(Model):
    """
    AttributeGroupDescription model
    
    Represents the attribute_group_description table in the OpenCart database.
    
    Attributes:
        attribute_group_id (int(11)) - Primary key
        language_id (int(11)) - Primary key
        name (varchar(64)), nullable
    """

    attribute_group_id = fields.IntField(null=True)
    language_id = fields.IntField(null=True)
    name = fields.CharField(max_length=64, null=True)

    class Meta:
        table = "oc_attribute_group_description"
        unique_together = (("attribute_group_id", "language_id"),)

    async def get_attribute_group(self):
        """Get related AttributeGroup"""
        if self.attribute_group_id:
            return await AttributeGroup.get(attribute_group_id=self.attribute_group_id)
        return None
    async def get_language(self):
        """Get related Language"""
        if self.language_id:
            return await Language.get(language_id=self.language_id)
        return None
