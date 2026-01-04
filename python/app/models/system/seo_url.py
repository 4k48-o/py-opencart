"""
Tortoise ORM model for seo_url table
"""

from tortoise.models import Model
from tortoise import fields
from .store import Store
from ..localisation.language import Language


class SeoUrl(Model):
    """
    SeoUrl model
    
    Represents the seo_url table in the OpenCart database.
    
    Attributes:
        seo_url_id (int(11)) - Primary key
        store_id (int(11)), nullable, default: 0
        language_id (int(11)), nullable
        key (varchar(64)), nullable
        value (varchar(255)), nullable
        keyword (varchar(768)), nullable
        sort_order (int(3)), nullable, default: 0
    """

    seo_url_id = fields.IntField(pk=True)
    store_id = fields.IntField(null=True, default=0)
    language_id = fields.IntField(null=True)
    key = fields.CharField(max_length=64, null=True)
    value = fields.CharField(max_length=255, null=True)
    keyword = fields.CharField(max_length=768, null=True)
    sort_order = fields.IntField(null=True, default=0)

    class Meta:
        table = "oc_seo_url"
        indexes = [("store_id",), ("language_id",), ("keyword",), ("key", "value",)]

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
