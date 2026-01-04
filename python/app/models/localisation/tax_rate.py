"""
Tortoise ORM model for tax_rate table
"""

from tortoise.models import Model
from tortoise import fields
from .geo_zone import GeoZone


class TaxRate(Model):
    """
    TaxRate model
    
    Represents the tax_rate table in the OpenCart database.
    
    Attributes:
        tax_rate_id (int(11)) - Primary key
        geo_zone_id (int(11)), nullable, default: 0
        name (varchar(32)), nullable
        rate (decimal(15,4)), nullable, default: 0.0000
        type (char(1)), nullable
    """

    tax_rate_id = fields.IntField(pk=True)
    geo_zone_id = fields.IntField(null=True, default=0)
    name = fields.CharField(max_length=32, null=True)
    rate = fields.DecimalField(max_digits=15, decimal_places=4, null=True, default='0.0000')
    type = fields.CharField(max_length=1, null=True)

    class Meta:
        table = "oc_tax_rate"

    async def get_geo_zone(self):
        """Get related GeoZone"""
        if self.geo_zone_id:
            return await GeoZone.get(geo_zone_id=self.geo_zone_id)
        return None
