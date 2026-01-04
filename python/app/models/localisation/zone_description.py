"""
Tortoise ORM model for zone_description table
"""

from tortoise.models import Model
from tortoise import fields
from .language import Language


class ZoneDescription(Model):
    """
    ZoneDescription model
    
    Represents the zone_description table in the OpenCart database.
    
    Attributes:
        zone_id (int(11)) - Primary key
        language_id (int(11)) - Primary key
        name (varchar(255)), nullable
    """

    zone_id = fields.IntField(null=True)
    language_id = fields.IntField(null=True)
    name = fields.CharField(max_length=255, null=True)

    class Meta:
        table = "oc_zone_description"
        indexes = [("name",)]
        unique_together = (("zone_id", "language_id"),)

    async def get_language(self):
        """Get related Language"""
        if self.language_id:
            return await Language.get(language_id=self.language_id)
        return None
