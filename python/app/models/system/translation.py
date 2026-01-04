"""
Tortoise ORM model for translation table
"""

from tortoise.models import Model
from tortoise import fields
from .store import Store
from ..localisation.language import Language


class Translation(Model):
    """
    Translation model
    
    Represents the translation table in the OpenCart database.
    
    Attributes:
        translation_id (int(11)) - Primary key
        store_id (int(11)), nullable, default: 0
        language_id (int(11)), nullable
        route (varchar(64)), nullable
        key (varchar(64)), nullable
        value (text), nullable
        date_added (datetime), nullable
    """

    translation_id = fields.IntField(pk=True)
    store_id = fields.IntField(null=True, default=0)
    language_id = fields.IntField(null=True)
    route = fields.CharField(max_length=64, null=True)
    key = fields.CharField(max_length=64, null=True)
    value = fields.TextField(null=True)
    date_added = fields.DatetimeField(null=True)

    class Meta:
        table = "oc_translation"

    async def get_store(self):
        """Get related Store"""
        if self.store_id:
            return await Store.get(store_id=self.store_id)
        return None
    async def get_language(self):
        """Get related Language"""
        if self.language_id:
            return await Language.get(language_id=self.language_id)
        return None
