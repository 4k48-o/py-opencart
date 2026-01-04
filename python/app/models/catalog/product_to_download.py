"""
Tortoise ORM model for product_to_download table
"""

from tortoise.models import Model
from tortoise import fields
from .product import Product
from .download import Download


class ProductToDownload(Model):
    """
    ProductToDownload model
    
    Represents the product_to_download table in the OpenCart database.
    
    Attributes:
        product_id (int(11)) - Primary key
        download_id (int(11)) - Primary key
    """

    product_id = fields.IntField(null=True)
    download_id = fields.IntField(null=True)

    class Meta:
        table = "oc_product_to_download"
        unique_together = (("product_id", "download_id"),)

    async def get_product(self):
        """Get related Product"""
        if self.product_id:
            return await Product.get(product_id=self.product_id)
        return None
    async def get_download(self):
        """Get related Download"""
        if self.download_id:
            return await Download.get(download_id=self.download_id)
        return None
