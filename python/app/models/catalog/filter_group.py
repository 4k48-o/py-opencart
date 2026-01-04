"""
Tortoise ORM model for filter_group table
"""

from tortoise.models import Model
from tortoise import fields


class FilterGroup(Model):
    """
    FilterGroup model
    
    Represents the filter_group table in the OpenCart database.
    
    Attributes:
        filter_group_id (int(11)) - Primary key
        sort_order (int(3)), nullable, default: 0
    """

    filter_group_id = fields.IntField(pk=True)
    sort_order = fields.IntField(null=True, default=0)

    class Meta:
        table = "oc_filter_group"

