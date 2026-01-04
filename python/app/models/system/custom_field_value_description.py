"""
Tortoise ORM model for custom_field_value_description table
"""

from tortoise.models import Model
from tortoise import fields
from ..localisation.language import Language
from .custom_field import CustomField


class CustomFieldValueDescription(Model):
    """
    CustomFieldValueDescription model
    
    Represents the custom_field_value_description table in the OpenCart database.
    
    Attributes:
        custom_field_value_id (int(11)) - Primary key
        language_id (int(11)) - Primary key
        custom_field_id (int(11)), nullable
        name (varchar(128)), nullable
    """

    custom_field_value_id = fields.IntField(null=True)
    language_id = fields.IntField(null=True)
    custom_field_id = fields.IntField(null=True)
    name = fields.CharField(max_length=128, null=True)

    class Meta:
        table = "oc_custom_field_value_description"
        unique_together = (("custom_field_value_id", "language_id"),)

    async def get_language(self):
        """Get related Language"""
        if self.language_id:
            return await Language.get(language_id=self.language_id)
        return None
    async def get_custom_field(self):
        """Get related CustomField"""
        if self.custom_field_id:
            return await CustomField.get(custom_field_id=self.custom_field_id)
        return None
