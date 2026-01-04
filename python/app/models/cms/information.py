"""
Tortoise ORM model for information table
"""

from tortoise.models import Model
from tortoise import fields


class Information(Model):
    """
    Information model
    
    Represents the information table in the OpenCart database.
    
    Attributes:
        information_id (int(11)) - Primary key
        sort_order (int(3)), nullable, default: 0
        status (tinyint(1)), nullable, default: 1
    """

    information_id = fields.IntField(pk=True)
    sort_order = fields.IntField(null=True, default=0)
    status = fields.SmallIntField(null=True, default=1)

    class Meta:
        table = "oc_information"

