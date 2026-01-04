"""
Tortoise ORM model for setting table
"""

from tortoise.models import Model
from tortoise import fields
from .store import Store


class Setting(Model):
    """
    Setting model
    
    Represents the setting table in the OpenCart database.
    
    Attributes:
        setting_id (int(11)) - Primary key
        store_id (int(11)), nullable, default: 0
        code (varchar(128)), nullable
        key (varchar(128)), nullable
        value (text), nullable
        serialized (tinyint(1)), nullable, default: 0
    """

    setting_id = fields.IntField(pk=True)
    store_id = fields.IntField(null=True, default=0)
    code = fields.CharField(max_length=128, null=True)
    key = fields.CharField(max_length=128, null=True)
    value = fields.TextField(null=True)
    serialized = fields.SmallIntField(null=True, default=0)

    class Meta:
        table = "oc_setting"

    async def get_store(self):
        """Get related Store"""
        if self.store_id:
            return await Store.get(store_id=self.store_id)
        return None
