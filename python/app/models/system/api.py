"""
Tortoise ORM model for api table
"""

from tortoise.models import Model
from tortoise import fields


class Api(Model):
    """
    Api model
    
    Represents the api table in the OpenCart database.
    
    Attributes:
        api_id (int(11)) - Primary key
        username (varchar(64)), nullable
        key (text), nullable
        status (tinyint(1)), nullable, default: 0
        date_added (datetime), nullable
        date_modified (datetime), nullable
    """

    api_id = fields.IntField(pk=True)
    username = fields.CharField(max_length=64, null=True)
    key = fields.TextField(null=True)
    status = fields.SmallIntField(null=True, default=0)
    date_added = fields.DatetimeField(null=True)
    date_modified = fields.DatetimeField(null=True)

    class Meta:
        table = "oc_api"

