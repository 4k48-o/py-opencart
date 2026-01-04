"""
Tortoise ORM model for modification table
"""

from tortoise.models import Model
from tortoise import fields


class Modification(Model):
    """
    Modification model
    
    Represents the modification table in the OpenCart database.
    
    Attributes:
        modification_id (int(11)) - Primary key
        extension_install_id (int(11))
        name (varchar(64)), nullable
        description (text), nullable
        code (varchar(64)), nullable
        author (varchar(64)), nullable
        version (varchar(32)), nullable
        link (varchar(255)), nullable
        xml (mediumtext), nullable
        status (tinyint(1)), nullable, default: 0
        date_added (datetime), nullable
    """

    modification_id = fields.IntField(pk=True)
    extension_install_id = fields.IntField()
    name = fields.CharField(max_length=64, null=True)
    description = fields.TextField(null=True)
    code = fields.CharField(max_length=64, null=True)
    author = fields.CharField(max_length=64, null=True)
    version = fields.CharField(max_length=32, null=True)
    link = fields.CharField(max_length=255, null=True)
    xml = fields.TextField(null=True)
    status = fields.SmallIntField(null=True, default=0)
    date_added = fields.DatetimeField(null=True)

    class Meta:
        table = "oc_modification"

