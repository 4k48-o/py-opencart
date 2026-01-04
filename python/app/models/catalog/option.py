"""
Tortoise ORM model for option table
"""

from tortoise.models import Model
from tortoise import fields


class Option(Model):
    """
    Option model
    
    Represents the option table in the OpenCart database.
    
    Attributes:
        option_id (int(11)) - Primary key
        type (varchar(32)), nullable
        validation (varchar(255)), nullable
        sort_order (int(3)), nullable, default: 0
    """

    option_id = fields.IntField(pk=True)
    type = fields.CharField(max_length=32, null=True)
    validation = fields.CharField(max_length=255, null=True)
    sort_order = fields.IntField(null=True, default=0)

    class Meta:
        table = "oc_option"

