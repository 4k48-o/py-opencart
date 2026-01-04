"""
Tortoise ORM model for product_description table
"""

from tortoise.models import Model
from tortoise import fields
from .product import Product
from ..localisation.language import Language


class ProductDescription(Model):
    """
    ProductDescription model
    
    Represents the product_description table in the OpenCart database.
    
    Attributes:
        product_id (int(11)) - Primary key
        language_id (int(11)) - Primary key
        name (varchar(255)), nullable
        description (text), nullable
        tag (text), nullable
        meta_title (varchar(255)), nullable
        meta_description (varchar(255)), nullable
        meta_keyword (varchar(255)), nullable
    """

    product_id = fields.IntField(null=True)
    language_id = fields.IntField(null=True)
    name = fields.CharField(max_length=255, null=True)
    description = fields.TextField(null=True)
    tag = fields.TextField(null=True)
    meta_title = fields.CharField(max_length=255, null=True)
    meta_description = fields.CharField(max_length=255, null=True)
    meta_keyword = fields.CharField(max_length=255, null=True)

    class Meta:
        table = "oc_product_description"
        indexes = [("name",)]
        unique_together = (("product_id", "language_id"),)

    async def get_product(self):
        """Get related Product"""
        if self.product_id:
            return await Product.get(product_id=self.product_id)
        return None
    async def get_language(self):
        """Get related Language"""
        if self.language_id:
            return await Language.get(language_id=self.language_id)
        return None
