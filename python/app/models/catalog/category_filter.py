"""
Tortoise ORM model for category_filter table
"""

from tortoise.models import Model
from tortoise import fields
from .category import Category
from .filter import Filter


class CategoryFilter(Model):
    """
    CategoryFilter model
    
    Represents the category_filter table in the OpenCart database.
    
    Attributes:
        category_id (int(11)) - Primary key
        filter_id (int(11)) - Primary key
    """

    category_id = fields.IntField(null=True)
    filter_id = fields.IntField(null=True)

    class Meta:
        table = "oc_category_filter"
        unique_together = (("category_id", "filter_id"),)

    async def get_category(self):
        """Get related Category"""
        if self.category_id:
            return await Category.get(category_id=self.category_id)
        return None
    async def get_filter(self):
        """Get related Filter"""
        if self.filter_id:
            return await Filter.get(filter_id=self.filter_id)
        return None
