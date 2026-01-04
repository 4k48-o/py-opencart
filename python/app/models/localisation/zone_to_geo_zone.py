"""
Tortoise ORM model for zone_to_geo_zone table
"""

from tortoise.models import Model
from tortoise import fields
from .geo_zone import GeoZone
from .country import Country
from .zone import Zone


class ZoneToGeoZone(Model):
    """
    ZoneToGeoZone model
    
    Represents the zone_to_geo_zone table in the OpenCart database.
    
    Attributes:
        zone_to_geo_zone_id (int(11)) - Primary key
        geo_zone_id (int(11)), nullable
        country_id (int(11)), nullable
        zone_id (int(11)), nullable, default: 0
    """

    zone_to_geo_zone_id = fields.IntField(pk=True)
    geo_zone_id = fields.IntField(null=True)
    country_id = fields.IntField(null=True)
    zone_id = fields.IntField(null=True, default=0)

    class Meta:
        table = "oc_zone_to_geo_zone"

    async def get_geo_zone(self):
        """Get related GeoZone"""
        if self.geo_zone_id:
            return await GeoZone.get(geo_zone_id=self.geo_zone_id)
        return None
    async def get_country(self):
        """Get related Country"""
        if self.country_id:
            return await Country.get(country_id=self.country_id)
        return None
    async def get_zone(self):
        """Get related Zone"""
        if self.zone_id:
            return await Zone.get(zone_id=self.zone_id)
        return None
