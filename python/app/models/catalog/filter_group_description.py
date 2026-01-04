"""
Tortoise ORM model for filter_group_description table
"""

from tortoise.models import Model
from tortoise import fields
from .filter_group import FilterGroup
from ..localisation.language import Language


class FilterGroupDescription(Model):
    """
    FilterGroupDescription model
    
    Represents the filter_group_description table in the OpenCart database.
    
    Attributes:
        filter_group_id (int(11)) - Primary key
        language_id (int(11)) - Primary key
        name (varchar(64)), nullable
    """

    filter_group_id = fields.IntField(null=True)
    language_id = fields.IntField(null=True)
    name = fields.CharField(max_length=64, null=True)

    class Meta:
        table = "oc_filter_group_description"
        unique_together = (("filter_group_id", "language_id"),)

    async def get_filter_group(self):
        """Get related FilterGroup"""
        if self.filter_group_id:
            return await FilterGroup.get(filter_group_id=self.filter_group_id)
        return None
    async def get_language(self):
        """Get related Language"""
        if self.language_id:
            return await Language.get(language_id=self.language_id)
        return None
