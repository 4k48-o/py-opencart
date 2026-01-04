"""
Tortoise ORM model for layout table
"""

from tortoise.models import Model
from tortoise import fields


class Layout(Model):
    """
    Layout model
    
    Represents the layout table in the OpenCart database.
    
    Attributes:
        layout_id (int(11)) - Primary key
        name (varchar(64)), nullable
    """

    layout_id = fields.IntField(pk=True)
    name = fields.CharField(max_length=64, null=True)

    class Meta:
        table = "oc_layout"

