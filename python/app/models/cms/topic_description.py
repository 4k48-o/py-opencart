"""
Tortoise ORM model for topic_description table
"""

from tortoise.models import Model
from tortoise import fields
from ..localisation.language import Language


class TopicDescription(Model):
    """
    TopicDescription model
    
    Represents the topic_description table in the OpenCart database.
    
    Attributes:
        topic_id (int(11)) - Primary key
        language_id (int(11)) - Primary key
        name (varchar(255)), nullable
        description (text), nullable
        image (varchar(255)), nullable
        meta_title (varchar(255)), nullable
        meta_description (varchar(255)), nullable
        meta_keyword (varchar(255)), nullable
    """

    topic_id = fields.IntField(null=True)
    language_id = fields.IntField(null=True)
    name = fields.CharField(max_length=255, null=True)
    description = fields.TextField(null=True)
    image = fields.CharField(max_length=255, null=True)
    meta_title = fields.CharField(max_length=255, null=True)
    meta_description = fields.CharField(max_length=255, null=True)
    meta_keyword = fields.CharField(max_length=255, null=True)

    class Meta:
        table = "oc_topic_description"
        indexes = [("name",)]
        unique_together = (("topic_id", "language_id"),)

    async def get_language(self):
        """Get related Language"""
        if self.language_id:
            return await Language.get(language_id=self.language_id)
        return None
