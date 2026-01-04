"""
Tortoise ORM model for download_description table
"""

from tortoise.models import Model
from tortoise import fields
from ..localisation.language import Language


class DownloadDescription(Model):
    """
    DownloadDescription model
    
    Represents the download_description table in the OpenCart database.
    
    Attributes:
        download_id (int(11)) - Primary key
        language_id (int(11)) - Primary key
        name (varchar(64)), nullable
    """

    download_id = fields.IntField(null=True)
    language_id = fields.IntField(null=True)
    name = fields.CharField(max_length=64, null=True)

    class Meta:
        table = "oc_download_description"
        unique_together = (("download_id", "language_id"),)

    async def get_language(self):
        """Get related Language"""
        if self.language_id:
            return await Language.get(language_id=self.language_id)
        return None
