"""
Tortoise ORM model for category_to_store table
"""

from tortoise.models import Model
from tortoise import fields
from .category import Category
from ..system.store import Store


class CategoryToStore(Model):
    """
    CategoryToStore model
    
    Represents the category_to_store table in the OpenCart database.
    
    Attributes:
        category_id (int(11)) - Primary key
        store_id (int(11)) - Primary key, default: 0
    """

    category_id = fields.IntField(null=True)
    store_id = fields.IntField(null=True, default=0)

    class Meta:
        table = "oc_category_to_store"
        unique_together = (("category_id", "store_id"),)

    async def get_category(self):
        """Get related Category"""
        if self.category_id:
            return await Category.get(category_id=self.category_id)
        return None
    async def get_store(self):
        """Get related Store"""
        if self.store_id:
            return await Store.get(store_id=self.store_id)
        return None
