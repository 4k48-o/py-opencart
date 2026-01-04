"""
Tortoise ORM model for extension_install table
"""

from tortoise.models import Model
from tortoise import fields
from .extension import Extension


class ExtensionInstall(Model):
    """
    ExtensionInstall model
    
    Represents the extension_install table in the OpenCart database.
    
    Attributes:
        extension_install_id (int(11)) - Primary key
        extension_id (int(11)), nullable, default: 0
        extension_download_id (int(11)), nullable, default: 0
        name (varchar(128)), nullable
        description (text), nullable
        code (varchar(255)), nullable
        version (varchar(255)), nullable
        author (varchar(255)), nullable
        link (varchar(255)), nullable
        status (tinyint(1)), nullable, default: 0
        date_added (datetime), nullable
    """

    extension_install_id = fields.IntField(pk=True)
    extension_id = fields.IntField(null=True, default=0)
    extension_download_id = fields.IntField(null=True, default=0)
    name = fields.CharField(max_length=128, null=True)
    description = fields.TextField(null=True)
    code = fields.CharField(max_length=255, null=True)
    version = fields.CharField(max_length=255, null=True)
    author = fields.CharField(max_length=255, null=True)
    link = fields.CharField(max_length=255, null=True)
    status = fields.SmallIntField(null=True, default=0)
    date_added = fields.DatetimeField(null=True)

    class Meta:
        table = "oc_extension_install"

    async def get_extension(self):
        """Get related Extension"""
        if self.extension_id:
            return await Extension.get(extension_id=self.extension_id)
        return None
