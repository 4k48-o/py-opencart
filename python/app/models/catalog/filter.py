"""
Tortoise ORM model for filter table
"""

from tortoise.models import Model
from tortoise import fields
from .filter_group import FilterGroup


class Filter(Model):
    """
    Filter model
    
    Represents the filter table in the OpenCart database.
    
    Attributes:
        filter_id (int(11)) - Primary key
        filter_group_id (int(11)), nullable
        sort_order (int(3)), nullable, default: 0
    """

    filter_id = fields.IntField(pk=True)
    filter_group_id = fields.IntField(null=True)
    sort_order = fields.IntField(null=True, default=0)

    class Meta:
        table = "oc_filter"

    async def get_filter_group(self):
        """Get related FilterGroup"""
        if self.filter_group_id:
            return await FilterGroup.get(filter_group_id=self.filter_group_id)
        return None
