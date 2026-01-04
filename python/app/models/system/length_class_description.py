"""
Tortoise ORM model for length_class_description table
"""

from tortoise.models import Model
from tortoise import fields
from ..localisation.length_class import LengthClass
from ..localisation.language import Language


class LengthClassDescription(Model):
    """
    LengthClassDescription model
    
    Represents the length_class_description table in the OpenCart database.
    
    Attributes:
        length_class_id (int(11)) - Primary key
        language_id (int(11)) - Primary key
        title (varchar(32)), nullable
        unit (varchar(4)), nullable
    """

    length_class_id = fields.IntField(null=True)
    language_id = fields.IntField(null=True)
    title = fields.CharField(max_length=32, null=True)
    unit = fields.CharField(max_length=4, null=True)

    class Meta:
        table = "oc_length_class_description"
        unique_together = (("length_class_id", "language_id"),)

    async def get_length_class(self):
        """Get related LengthClass"""
        if self.length_class_id:
            return await LengthClass.get(length_class_id=self.length_class_id)
        return None
    async def get_language(self):
        """Get related Language"""
        if self.language_id:
            return await Language.get(language_id=self.language_id)
        return None
