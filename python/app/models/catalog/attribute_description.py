"""
Tortoise ORM model for attribute_description table
"""

from tortoise.models import Model
from tortoise import fields
from .attribute import Attribute
from ..localisation.language import Language


class AttributeDescription(Model):
    """
    AttributeDescription model
    
    Represents the attribute_description table in the OpenCart database.
    
    Attributes:
        attribute_id (int(11)) - Primary key
        language_id (int(11)) - Primary key
        name (varchar(64)), nullable
    """

    attribute_id = fields.IntField(null=True)
    language_id = fields.IntField(null=True)
    name = fields.CharField(max_length=64, null=True)

    class Meta:
        table = "oc_attribute_description"
        unique_together = (("attribute_id", "language_id"),)

    async def get_attribute(self):
        """Get related Attribute"""
        if self.attribute_id:
            return await Attribute.get(attribute_id=self.attribute_id)
        return None
    async def get_language(self):
        """Get related Language"""
        if self.language_id:
            return await Language.get(language_id=self.language_id)
        return None
