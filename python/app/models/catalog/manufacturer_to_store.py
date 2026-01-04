"""
Tortoise ORM model for manufacturer_to_store table
"""

from tortoise.models import Model
from tortoise import fields
from .manufacturer import Manufacturer
from ..system.store import Store


class ManufacturerToStore(Model):
    """
    ManufacturerToStore model
    
    Represents the manufacturer_to_store table in the OpenCart database.
    
    Attributes:
        manufacturer_id (int(11)) - Primary key
        store_id (int(11)) - Primary key, default: 0
    """

    manufacturer_id = fields.IntField(null=True)
    store_id = fields.IntField(null=True, default=0)

    class Meta:
        table = "oc_manufacturer_to_store"
        unique_together = (("manufacturer_id", "store_id"),)

    async def get_manufacturer(self):
        """Get related Manufacturer"""
        if self.manufacturer_id:
            return await Manufacturer.get(manufacturer_id=self.manufacturer_id)
        return None
    async def get_store(self):
        """Get related Store"""
        if self.store_id:
            return await Store.get(store_id=self.store_id)
        return None
