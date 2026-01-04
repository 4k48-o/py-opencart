"""
Tortoise ORM model for geo_zone table
"""

from tortoise.models import Model
from tortoise import fields


class GeoZone(Model):
    """
    GeoZone model
    
    Represents the geo_zone table in the OpenCart database.
    
    Attributes:
        geo_zone_id (int(11)) - Primary key
        name (varchar(32)), nullable
        description (varchar(255)), nullable
    """

    geo_zone_id = fields.IntField(pk=True)
    name = fields.CharField(max_length=32, null=True)
    description = fields.CharField(max_length=255, null=True)

    class Meta:
        table = "oc_geo_zone"

