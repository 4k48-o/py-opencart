"""
Tortoise ORM model for category_path table
"""

from tortoise.models import Model
from tortoise import fields
from .category import Category


class CategoryPath(Model):
    """
    CategoryPath model
    
    Represents the category_path table in the OpenCart database.
    
    Attributes:
        category_id (int(11)) - Primary key
        path_id (int(11)) - Primary key
        level (int(11)), nullable
    """

    category_id = fields.IntField(null=True)
    path_id = fields.IntField(null=True)
    level = fields.IntField(null=True)

    class Meta:
        table = "oc_category_path"
        unique_together = (("category_id", "path_id"),)

    async def get_category(self):
        """Get related Category"""
        if self.category_id:
            return await Category.get(category_id=self.category_id)
        return None
