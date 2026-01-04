"""
Tortoise ORM model for gdpr table
"""

from tortoise.models import Model
from tortoise import fields
from .store import Store
from ..localisation.language import Language


class Gdpr(Model):
    """
    Gdpr model
    
    Represents the gdpr table in the OpenCart database.
    
    Attributes:
        gdpr_id (int(11)) - Primary key
        store_id (int(11)), nullable, default: 0
        language_id (int(11)), nullable
        code (varchar(40)), nullable
        email (varchar(96)), nullable
        action (varchar(6)), nullable
        status (tinyint(1)), nullable, default: 0
        date_added (datetime), nullable
    """

    gdpr_id = fields.IntField(pk=True)
    store_id = fields.IntField(null=True, default=0)
    language_id = fields.IntField(null=True)
    code = fields.CharField(max_length=40, null=True)
    email = fields.CharField(max_length=96, null=True)
    action = fields.CharField(max_length=6, null=True)
    status = fields.SmallIntField(null=True, default=0)
    date_added = fields.DatetimeField(null=True)

    class Meta:
        table = "oc_gdpr"

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
