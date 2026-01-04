"""
Tortoise ORM model for topic table
"""

from tortoise.models import Model
from tortoise import fields


class Topic(Model):
    """
    Topic model
    
    Represents the topic table in the OpenCart database.
    
    Attributes:
        topic_id (int(11)) - Primary key
        sort_order (int(3)), nullable, default: 0
        status (tinyint(1)), nullable, default: 0
    """

    topic_id = fields.IntField(pk=True)
    sort_order = fields.IntField(null=True, default=0)
    status = fields.SmallIntField(null=True, default=0)

    class Meta:
        table = "oc_topic"

