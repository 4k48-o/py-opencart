"""
Tortoise ORM model for article table
"""

from tortoise.models import Model
from tortoise import fields


class Article(Model):
    """
    Article model
    
    Represents the article table in the OpenCart database.
    
    Attributes:
        article_id (int(11)) - Primary key
        topic_id (int(11)), nullable, default: 0
        author (varchar(64)), nullable
        rating (int(11)), nullable, default: 0
        status (tinyint(1)), nullable, default: 0
        date_added (datetime), nullable
        date_modified (datetime), nullable
    """

    article_id = fields.IntField(pk=True)
    topic_id = fields.IntField(null=True, default=0)
    author = fields.CharField(max_length=64, null=True)
    rating = fields.IntField(null=True, default=0)
    status = fields.SmallIntField(null=True, default=0)
    date_added = fields.DatetimeField(null=True)
    date_modified = fields.DatetimeField(null=True)

    class Meta:
        table = "oc_article"

