"""
Tortoise ORM model for location table
"""

from tortoise.models import Model
from tortoise import fields


class Location(Model):
    """
    Location model
    
    Represents the location table in the OpenCart database.
    
    Attributes:
        location_id (int(11)) - Primary key
        name (varchar(32)), nullable
        address (text), nullable
        telephone (varchar(32)), nullable
        geocode (varchar(32)), nullable
        image (varchar(255)), nullable
        open (text), nullable
        comment (text), nullable
    """

    location_id = fields.IntField(pk=True)
    name = fields.CharField(max_length=32, null=True)
    address = fields.TextField(null=True)
    telephone = fields.CharField(max_length=32, null=True)
    geocode = fields.CharField(max_length=32, null=True)
    image = fields.CharField(max_length=255, null=True)
    open = fields.TextField(null=True)
    comment = fields.TextField(null=True)

    class Meta:
        table = "oc_location"
        indexes = [("name",)]

