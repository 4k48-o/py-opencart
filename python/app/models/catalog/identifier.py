"""
Tortoise ORM model for identifier table
"""

from tortoise.models import Model
from tortoise import fields


class Identifier(Model):
    """
    Identifier model
    
    Represents the identifier table in the OpenCart database.
    
    Attributes:
        identifier_id (int(11)) - Primary key
        name (varchar(64)), nullable
        code (varchar(48)), nullable
        validation (varchar(255)), nullable
        status (tinyint(1)), nullable, default: 0
    """

    identifier_id = fields.IntField(pk=True)
    name = fields.CharField(max_length=64, null=True)
    code = fields.CharField(max_length=48, null=True)
    validation = fields.CharField(max_length=255, null=True)
    status = fields.SmallIntField(null=True, default=0)

    class Meta:
        table = "oc_identifier"

