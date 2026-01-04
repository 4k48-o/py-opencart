"""
Tortoise ORM model for cron table
"""

from tortoise.models import Model
from tortoise import fields


class Cron(Model):
    """
    Cron model
    
    Represents the cron table in the OpenCart database.
    
    Attributes:
        cron_id (int(11)) - Primary key
        code (varchar(128)), nullable
        description (text), nullable
        cycle (varchar(12)), nullable
        action (text), nullable
        status (tinyint(1)), nullable, default: 0
        date_added (datetime), nullable
        date_modified (datetime), nullable
    """

    cron_id = fields.IntField(pk=True)
    code = fields.CharField(max_length=128, null=True)
    description = fields.TextField(null=True)
    cycle = fields.CharField(max_length=12, null=True)
    action = fields.TextField(null=True)
    status = fields.SmallIntField(null=True, default=0)
    date_added = fields.DatetimeField(null=True)
    date_modified = fields.DatetimeField(null=True)

    class Meta:
        table = "oc_cron"

