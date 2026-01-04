"""
Tortoise ORM model for marketing table
"""

from tortoise.models import Model
from tortoise import fields


class Marketing(Model):
    """
    Marketing model
    
    Represents the marketing table in the OpenCart database.
    
    Attributes:
        marketing_id (int(11)) - Primary key
        name (varchar(32)), nullable
        description (text), nullable
        code (varchar(64)), nullable
        clicks (int(5)), nullable, default: 0
        date_added (datetime), nullable
    """

    marketing_id = fields.IntField(pk=True)
    name = fields.CharField(max_length=32, null=True)
    description = fields.TextField(null=True)
    code = fields.CharField(max_length=64, null=True)
    clicks = fields.IntField(null=True, default=0)
    date_added = fields.DatetimeField(null=True)

    class Meta:
        table = "oc_marketing"

