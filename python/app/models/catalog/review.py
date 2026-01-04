"""
Tortoise ORM model for review table
"""

from tortoise.models import Model
from tortoise import fields
from .product import Product
from ..customer.customer import Customer


class Review(Model):
    """
    Review model
    
    Represents the review table in the OpenCart database.
    
    Attributes:
        review_id (int(11)) - Primary key
        product_id (int(11)), nullable, default: 0
        customer_id (int(11)), nullable, default: 0
        author (varchar(64)), nullable
        text (text), nullable
        rating (int(1)), nullable, default: 0
        status (tinyint(1)), nullable, default: 0
        date_added (datetime), nullable
        date_modified (datetime), nullable
    """

    review_id = fields.IntField(pk=True)
    product_id = fields.IntField(null=True, default=0)
    customer_id = fields.IntField(null=True, default=0)
    author = fields.CharField(max_length=64, null=True)
    text = fields.TextField(null=True)
    rating = fields.IntField(null=True, default=0)
    status = fields.SmallIntField(null=True, default=0)
    date_added = fields.DatetimeField(null=True)
    date_modified = fields.DatetimeField(null=True)

    class Meta:
        table = "oc_review"
        indexes = [("product_id",)]

    async def get_product(self):
        """Get related Product"""
        if self.product_id:
            return await Product.get(product_id=self.product_id)
        return None
    async def get_customer(self):
        """Get related Customer"""
        if self.customer_id:
            return await Customer.get(customer_id=self.customer_id)
        return None
