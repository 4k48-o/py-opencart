"""
Tortoise ORM model for layout_module table
"""

from tortoise.models import Model
from tortoise import fields
from .layout import Layout


class LayoutModule(Model):
    """
    LayoutModule model
    
    Represents the layout_module table in the OpenCart database.
    
    Attributes:
        layout_module_id (int(11)) - Primary key
        layout_id (int(11)), nullable, default: 0
        code (varchar(64)), nullable
        position (varchar(14)), nullable
        sort_order (int(3)), nullable, default: 0
    """

    layout_module_id = fields.IntField(pk=True)
    layout_id = fields.IntField(null=True, default=0)
    code = fields.CharField(max_length=64, null=True)
    position = fields.CharField(max_length=14, null=True)
    sort_order = fields.IntField(null=True, default=0)

    class Meta:
        table = "oc_layout_module"

    async def get_layout(self):
        """Get related Layout"""
        if self.layout_id:
            return await Layout.get(layout_id=self.layout_id)
        return None
