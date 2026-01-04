"""
Tortoise ORM model for startup table
"""

from tortoise.models import Model
from tortoise import fields


class Startup(Model):
    """
    Startup model
    
    Represents the startup table in the OpenCart database.
    
    Attributes:
        startup_id (int(11)) - Primary key
        description (text), nullable
        code (varchar(64)), nullable
        action (text), nullable
        status (tinyint(1)), nullable, default: 0
        sort_order (int(3)), nullable, default: 0
    """

    startup_id = fields.IntField(pk=True)
    description = fields.TextField(null=True)
    code = fields.CharField(max_length=64, null=True)
    action = fields.TextField(null=True)
    status = fields.SmallIntField(null=True, default=0)
    sort_order = fields.IntField(null=True, default=0)

    class Meta:
        table = "oc_startup"

