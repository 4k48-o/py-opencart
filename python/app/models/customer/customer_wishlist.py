"""
Tortoise ORM model for customer_wishlist table
"""

from tortoise.models import Model
from tortoise import fields
from .customer import Customer
from ..system.store import Store
from ..catalog.product import Product


class CustomerWishlist(Model):
    """
    CustomerWishlist model
    
    Represents the customer_wishlist table in the OpenCart database.
    
    Attributes:
        customer_id (int(11)) - Primary key
        store_id (int(11)) - Primary key, default: 0
        product_id (int(11)) - Primary key
        date_added (datetime), nullable
    """

    customer_id = fields.IntField(null=True)
    store_id = fields.IntField(null=True, default=0)
    product_id = fields.IntField(null=True)
    date_added = fields.DatetimeField(null=True)

    class Meta:
        table = "oc_customer_wishlist"
        unique_together = (("customer_id", "store_id", "product_id"),)

    async def get_customer(self):
        """Get related Customer"""
        if self.customer_id:
            return await Customer.get(customer_id=self.customer_id)
        return None
    async def get_store(self):
        """Get related Store"""
        if self.store_id:
            return await Store.get(store_id=self.store_id)
        return None
    async def get_product(self):
        """Get related Product"""
        if self.product_id:
            return await Product.get(product_id=self.product_id)
        return None
