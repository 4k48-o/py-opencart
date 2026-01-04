"""
Tortoise ORM model for event table
"""

from tortoise.models import Model
from tortoise import fields


class Event(Model):
    """
    Event model
    
    Represents the event table in the OpenCart database.
    
    Attributes:
        event_id (int(11)) - Primary key
        code (varchar(128)), nullable
        description (text), nullable
        trigger (text), nullable
        action (text), nullable
        status (tinyint(1)), nullable, default: 0
        sort_order (int(3)), nullable, default: 1
    """

    event_id = fields.IntField(pk=True)
    code = fields.CharField(max_length=128, null=True)
    description = fields.TextField(null=True)
    trigger = fields.TextField(null=True)
    action = fields.TextField(null=True)
    status = fields.SmallIntField(null=True, default=0)
    sort_order = fields.IntField(null=True, default=1)

    class Meta:
        table = "oc_event"

