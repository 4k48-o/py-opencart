"""
Tortoise ORM model for coupon_product table
"""

from tortoise.models import Model
from tortoise import fields
from .coupon import Coupon
from ..catalog.product import Product


class CouponProduct(Model):
    """
    CouponProduct model
    
    Represents the coupon_product table in the OpenCart database.
    
    Attributes:
        coupon_product_id (int(11)) - Primary key
        coupon_id (int(11)), nullable
        product_id (int(11)), nullable
    """

    coupon_product_id = fields.IntField(pk=True)
    coupon_id = fields.IntField(null=True)
    product_id = fields.IntField(null=True)

    class Meta:
        table = "oc_coupon_product"

    async def get_coupon(self):
        """Get related Coupon"""
        if self.coupon_id:
            return await Coupon.get(coupon_id=self.coupon_id)
        return None
    async def get_product(self):
        """Get related Product"""
        if self.product_id:
            return await Product.get(product_id=self.product_id)
        return None
