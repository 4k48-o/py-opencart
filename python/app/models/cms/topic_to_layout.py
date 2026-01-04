"""
Tortoise ORM model for topic_to_layout table
"""

from tortoise.models import Model
from tortoise import fields
from .topic import Topic
from ..system.store import Store
from ..design.layout import Layout


class TopicToLayout(Model):
    """
    TopicToLayout model
    
    Represents the topic_to_layout table in the OpenCart database.
    
    Attributes:
        topic_id (int(11)) - Primary key
        store_id (int(11)) - Primary key, default: 0
        layout_id (int(11)), nullable, default: 0
    """

    topic_id = fields.IntField(null=True)
    store_id = fields.IntField(null=True, default=0)
    layout_id = fields.IntField(null=True, default=0)

    class Meta:
        table = "oc_topic_to_layout"
        unique_together = (("topic_id", "store_id"),)

    async def get_topic(self):
        """Get related Topic"""
        if self.topic_id:
            return await Topic.get(topic_id=self.topic_id)
        return None
    async def get_store(self):
        """Get related Store"""
        if self.store_id:
            return await Store.get(store_id=self.store_id)
        return None
    async def get_layout(self):
        """Get related Layout"""
        if self.layout_id:
            return await Layout.get(layout_id=self.layout_id)
        return None
