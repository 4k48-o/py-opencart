"""
Tortoise ORM model for theme table
"""

from tortoise.models import Model
from tortoise import fields
from ..system.store import Store


class Theme(Model):
    """
    Theme model
    
    Represents the theme table in the OpenCart database.
    
    Attributes:
        theme_id (int(11)) - Primary key
        store_id (int(11)), nullable, default: 0
        route (varchar(64)), nullable
        code (mediumtext), nullable
        status (tinyint(1)), nullable, default: 0
        date_added (datetime), nullable
    """

    theme_id = fields.IntField(pk=True)
    store_id = fields.IntField(null=True, default=0)
    route = fields.CharField(max_length=64, null=True)
    code = fields.TextField(null=True)
    status = fields.SmallIntField(null=True, default=0)
    date_added = fields.DatetimeField(null=True)

    class Meta:
        table = "oc_theme"

    async def get_store(self):
        """Get related Store"""
        if self.store_id:
            return await Store.get(store_id=self.store_id)
        return None
