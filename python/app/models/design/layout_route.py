"""
Tortoise ORM model for layout_route table
"""

from tortoise.models import Model
from tortoise import fields
from .layout import Layout
from ..system.store import Store


class LayoutRoute(Model):
    """
    LayoutRoute model
    
    Represents the layout_route table in the OpenCart database.
    
    Attributes:
        layout_route_id (int(11)) - Primary key
        layout_id (int(11)), nullable
        store_id (int(11)), nullable, default: 0
        route (varchar(64)), nullable
    """

    layout_route_id = fields.IntField(pk=True)
    layout_id = fields.IntField(null=True)
    store_id = fields.IntField(null=True, default=0)
    route = fields.CharField(max_length=64, null=True)

    class Meta:
        table = "oc_layout_route"

    async def get_layout(self):
        """Get related Layout"""
        if self.layout_id:
            return await Layout.get(layout_id=self.layout_id)
        return None
    async def get_store(self):
        """Get related Store"""
        if self.store_id:
            return await Store.get(store_id=self.store_id)
        return None
