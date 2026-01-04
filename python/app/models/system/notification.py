"""
Tortoise ORM model for notification table
"""

from tortoise.models import Model
from tortoise import fields


class Notification(Model):
    """
    Notification model
    
    Represents the notification table in the OpenCart database.
    
    Attributes:
        notification_id (int(11)) - Primary key
        title (varchar(64)), nullable
        text (text), nullable
        status (tinyint(11)), nullable, default: 0
        date_added (datetime), nullable
    """

    notification_id = fields.IntField(pk=True)
    title = fields.CharField(max_length=64, null=True)
    text = fields.TextField(null=True)
    status = fields.SmallIntField(null=True, default=0)
    date_added = fields.DatetimeField(null=True)

    class Meta:
        table = "oc_notification"

