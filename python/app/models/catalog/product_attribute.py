"""
Tortoise ORM model for product_attribute table
"""

from tortoise.models import Model
from tortoise import fields
from .product import Product
from .attribute import Attribute
from ..localisation.language import Language


class ProductAttribute(Model):
    """
    ProductAttribute model
    
    Represents the product_attribute table in the OpenCart database.
    
    Attributes:
        product_id (int(11)) - Primary key
        attribute_id (int(11)) - Primary key
        language_id (int(11)) - Primary key
        text (text), nullable
    """

    product_id = fields.IntField(null=True)
    attribute_id = fields.IntField(null=True)
    language_id = fields.IntField(null=True)
    text = fields.TextField(null=True)

    class Meta:
        table = "oc_product_attribute"
        unique_together = (("product_id", "attribute_id", "language_id"),)

    async def get_product(self):
        """Get related Product"""
        if self.product_id:
            return await Product.get(product_id=self.product_id)
        return None
    async def get_attribute(self):
        """Get related Attribute"""
        if self.attribute_id:
            return await Attribute.get(attribute_id=self.attribute_id)
        return None
    async def get_language(self):
        """Get related Language"""
        if self.language_id:
            return await Language.get(language_id=self.language_id)
        return None
