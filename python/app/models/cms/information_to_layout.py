"""
Tortoise ORM model for information_to_layout table
"""

from tortoise.models import Model
from tortoise import fields
from .information import Information
from ..system.store import Store
from ..design.layout import Layout


class InformationToLayout(Model):
    """
    InformationToLayout model
    
    Represents the information_to_layout table in the OpenCart database.
    
    Attributes:
        information_id (int(11)) - Primary key
        store_id (int(11)) - Primary key, default: 0
        layout_id (int(11)), nullable, default: 0
    """

    information_id = fields.IntField(null=True)
    store_id = fields.IntField(null=True, default=0)
    layout_id = fields.IntField(null=True, default=0)

    class Meta:
        table = "oc_information_to_layout"
        unique_together = (("information_id", "store_id"),)

    async def get_information(self):
        """Get related Information"""
        if self.information_id:
            return await Information.get(information_id=self.information_id)
        return None
    async def get_store(self):
        """Get related Store"""
        if self.store_id:
            return await Store.get(store_id=self.store_id)
        return None
    async def get_layout(self):
        """Get related Layout"""
        if self.layout_id:
            return await Layout.get(layout_id=self.layout_id)
        return None
