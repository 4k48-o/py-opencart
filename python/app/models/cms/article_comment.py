"""
Tortoise ORM model for article_comment table
"""

from tortoise.models import Model
from tortoise import fields
from .article import Article
from ..customer.customer import Customer


class ArticleComment(Model):
    """
    ArticleComment model
    
    Represents the article_comment table in the OpenCart database.
    
    Attributes:
        article_comment_id (int(11)) - Primary key
        article_id (int(11)), nullable
        parent_id (int(11)), nullable, default: 0
        customer_id (int(11)), nullable, default: 0
        author (varchar(64)), nullable
        comment (text), nullable
        rating (int(11)), nullable, default: 0
        ip (varchar(40)), nullable
        status (tinyint(1)), nullable, default: 0
        date_added (datetime), nullable
    """

    article_comment_id = fields.IntField(pk=True)
    article_id = fields.IntField(null=True)
    parent_id = fields.IntField(null=True, default=0)
    customer_id = fields.IntField(null=True, default=0)
    author = fields.CharField(max_length=64, null=True)
    comment = fields.TextField(null=True)
    rating = fields.IntField(null=True, default=0)
    ip = fields.CharField(max_length=40, null=True)
    status = fields.SmallIntField(null=True, default=0)
    date_added = fields.DatetimeField(null=True)

    class Meta:
        table = "oc_article_comment"
        indexes = [("article_id",), ("customer_id",), ("parent_id",)]

    async def get_article(self):
        """Get related Article"""
        if self.article_id:
            return await Article.get(article_id=self.article_id)
        return None
    async def get_customer(self):
        """Get related Customer"""
        if self.customer_id:
            return await Customer.get(customer_id=self.customer_id)
        return None
