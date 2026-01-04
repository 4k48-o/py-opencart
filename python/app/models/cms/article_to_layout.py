"""
Tortoise ORM model for article_to_layout table
"""

from tortoise.models import Model
from tortoise import fields
from .article import Article
from ..system.store import Store
from ..design.layout import Layout


class ArticleToLayout(Model):
    """
    ArticleToLayout model
    
    Represents the article_to_layout table in the OpenCart database.
    
    Attributes:
        article_id (int(11)) - Primary key
        store_id (int(11)) - Primary key, default: 0
        layout_id (int(11)), nullable, default: 0
    """

    article_id = fields.IntField(null=True)
    store_id = fields.IntField(null=True, default=0)
    layout_id = fields.IntField(null=True, default=0)

    class Meta:
        table = "oc_article_to_layout"
        unique_together = (("article_id", "store_id"),)

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
    async def get_layout(self):
        """Get related Layout"""
        if self.layout_id:
            return await Layout.get(layout_id=self.layout_id)
        return None
