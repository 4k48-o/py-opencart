"""
Tortoise ORM model for country table
"""

from tortoise.models import Model
from tortoise import fields


class Country(Model):
    """
    Country model
    
    Represents the country table in the OpenCart database.
    
    Attributes:
        country_id (int(11)) - Primary key
        iso_code_2 (varchar(2)), nullable
        iso_code_3 (varchar(3)), nullable
        address_format_id (int(11)), nullable, default: 0
        postcode_required (tinyint(1)), nullable
        status (tinyint(1)), nullable, default: 1
    """

    country_id = fields.IntField(pk=True)
    iso_code_2 = fields.CharField(max_length=2, null=True)
    iso_code_3 = fields.CharField(max_length=3, null=True)
    address_format_id = fields.IntField(null=True, default=0)
    postcode_required = fields.SmallIntField(null=True)
    status = fields.SmallIntField(null=True, default=1)

    class Meta:
        table = "oc_country"

