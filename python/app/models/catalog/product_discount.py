"""
Tortoise ORM model for product_discount table
"""

from tortoise.models import Model
from tortoise import fields
from .product import Product
from ..customer.customer_group import CustomerGroup


class ProductDiscount(Model):
    """
    ProductDiscount model
    
    Represents the product_discount table in the OpenCart database.
    
    Attributes:
        product_discount_id (int(11)) - Primary key
        product_id (int(11)), nullable
        customer_group_id (int(11)), nullable
        quantity (int(4)), nullable, default: 0
        priority (int(5)), nullable, default: 1
        price (decimal(15,4)), nullable, default: 0.0000
        type (char(1)), nullable, default: P
        special (tinyint(1)), nullable, default: 0
        date_start (date), nullable
        date_end (date), nullable
    """

    product_discount_id = fields.IntField(pk=True)
    product_id = fields.IntField(null=True)
    customer_group_id = fields.IntField(null=True)
    quantity = fields.IntField(null=True, default=0)
    priority = fields.IntField(null=True, default=1)
    price = fields.DecimalField(max_digits=15, decimal_places=4, null=True, default='0.0000')
    type = fields.CharField(max_length=1, null=True, default='P')
    special = fields.SmallIntField(null=True, default=0)
    date_start = fields.DateField(null=True)
    date_end = fields.DateField(null=True)

    class Meta:
        table = "oc_product_discount"
        indexes = [("product_id",)]

    async def get_product(self):
        """Get related Product"""
        if self.product_id:
            return await Product.get(product_id=self.product_id)
        return None
    async def get_customer_group(self):
        """Get related CustomerGroup"""
        if self.customer_group_id:
            return await CustomerGroup.get(customer_group_id=self.customer_group_id)
        return None
