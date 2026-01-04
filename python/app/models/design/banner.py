"""
Tortoise ORM model for banner table
"""

from tortoise.models import Model
from tortoise import fields


class Banner(Model):
    """
    Banner model
    
    Represents the banner table in the OpenCart database.
    
    Attributes:
        banner_id (int(11)) - Primary key
        name (varchar(64)), nullable
        status (tinyint(1)), nullable, default: 0
    """

    banner_id = fields.IntField(pk=True)
    name = fields.CharField(max_length=64, null=True)
    status = fields.SmallIntField(null=True, default=0)

    class Meta:
        table = "oc_banner"

