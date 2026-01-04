"""
Tortoise ORM model for information_description table
"""

from tortoise.models import Model
from tortoise import fields
from ..localisation.language import Language


class InformationDescription(Model):
    """
    InformationDescription model
    
    Represents the information_description table in the OpenCart database.
    
    Attributes:
        information_id (int(11)) - Primary key
        language_id (int(11)) - Primary key
        title (varchar(64)), nullable
        description (mediumtext), nullable
        meta_title (varchar(255)), nullable
        meta_description (varchar(255)), nullable
        meta_keyword (varchar(255)), nullable
    """

    information_id = fields.IntField(null=True)
    language_id = fields.IntField(null=True)
    title = fields.CharField(max_length=64, null=True)
    description = fields.TextField(null=True)
    meta_title = fields.CharField(max_length=255, null=True)
    meta_description = fields.CharField(max_length=255, null=True)
    meta_keyword = fields.CharField(max_length=255, null=True)

    class Meta:
        table = "oc_information_description"
        unique_together = (("information_id", "language_id"),)

    async def get_language(self):
        """Get related Language"""
        if self.language_id:
            return await Language.get(language_id=self.language_id)
        return None
