"""
Tortoise ORM model for zone table
"""

from tortoise.models import Model
from tortoise import fields
from .country import Country


class Zone(Model):
    """
    Zone model
    
    Represents the zone table in the OpenCart database.
    
    Attributes:
        zone_id (int(11)) - Primary key
        country_id (int(11)), nullable
        code (varchar(32)), nullable
        status (tinyint(1)), nullable, default: 1
    """

    zone_id = fields.IntField(pk=True)
    country_id = fields.IntField(null=True)
    code = fields.CharField(max_length=32, null=True)
    status = fields.SmallIntField(null=True, default=1)

    class Meta:
        table = "oc_zone"

    async def get_country(self):
        """Get related Country"""
        if self.country_id:
            return await Country.get(country_id=self.country_id)
        return None
