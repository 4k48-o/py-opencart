"""
Tortoise ORM model for custom_field_value table
"""

from tortoise.models import Model
from tortoise import fields
from .custom_field import CustomField


class CustomFieldValue(Model):
    """
    CustomFieldValue model
    
    Represents the custom_field_value table in the OpenCart database.
    
    Attributes:
        custom_field_value_id (int(11)) - Primary key
        custom_field_id (int(11)), nullable
        sort_order (int(3)), nullable, default: 0
    """

    custom_field_value_id = fields.IntField(pk=True)
    custom_field_id = fields.IntField(null=True)
    sort_order = fields.IntField(null=True, default=0)

    class Meta:
        table = "oc_custom_field_value"

    async def get_custom_field(self):
        """Get related CustomField"""
        if self.custom_field_id:
            return await CustomField.get(custom_field_id=self.custom_field_id)
        return None
