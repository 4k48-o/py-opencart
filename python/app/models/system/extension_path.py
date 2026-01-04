"""
Tortoise ORM model for extension_path table
"""

from tortoise.models import Model
from tortoise import fields
from .extension_install import ExtensionInstall


class ExtensionPath(Model):
    """
    ExtensionPath model
    
    Represents the extension_path table in the OpenCart database.
    
    Attributes:
        extension_path_id (int(11)) - Primary key
        extension_install_id (int(11)), nullable
        path (varchar(255)), nullable
    """

    extension_path_id = fields.IntField(pk=True)
    extension_install_id = fields.IntField(null=True)
    path = fields.CharField(max_length=255, null=True)

    class Meta:
        table = "oc_extension_path"
        indexes = [("path",)]

    async def get_extension_install(self):
        """Get related ExtensionInstall"""
        if self.extension_install_id:
            return await ExtensionInstall.get(extension_install_id=self.extension_install_id)
        return None
