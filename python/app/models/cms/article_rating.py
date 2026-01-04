"""
Tortoise ORM model for article_rating table
"""

from tortoise.models import Model
from tortoise import fields
from .article_comment import ArticleComment
from .article import Article
from ..system.store import Store
from ..customer.customer import Customer


class ArticleRating(Model):
    """
    ArticleRating model
    
    Represents the article_rating table in the OpenCart database.
    
    Attributes:
        article_rating_id (int(11)) - Primary key
        article_comment_id (int(11)), nullable
        article_id (int(11)), nullable
        store_id (int(11)), nullable, default: 0
        customer_id (int(11)), nullable, default: 0
        rating (tinyint(1)), nullable, default: 0
        ip (varchar(40)), nullable
        date_added (datetime), nullable
    """

    article_rating_id = fields.IntField(pk=True)
    article_comment_id = fields.IntField(null=True)
    article_id = fields.IntField(null=True)
    store_id = fields.IntField(null=True, default=0)
    customer_id = fields.IntField(null=True, default=0)
    rating = fields.SmallIntField(null=True, default=0)
    ip = fields.CharField(max_length=40, null=True)
    date_added = fields.DatetimeField(null=True)

    class Meta:
        table = "oc_article_rating"
        indexes = [("article_comment_id",), ("article_id",), ("store_id",), ("customer_id",)]

    async def get_article_comment(self):
        """Get related ArticleComment"""
        if self.article_comment_id:
            return await ArticleComment.get(article_comment_id=self.article_comment_id)
        return None
    async def get_article(self):
        """Get related Article"""
        if self.article_id:
            return await Article.get(article_id=self.article_id)
        return None
    async def get_store(self):
        """Get related Store"""
        if self.store_id:
            return await Store.get(store_id=self.store_id)
        return None
    async def get_customer(self):
        """Get related Customer"""
        if self.customer_id:
            return await Customer.get(customer_id=self.customer_id)
        return None
