"""
Tortoise ORM model for coupon_category table
"""

from tortoise.models import Model
from tortoise import fields
from .coupon import Coupon
from ..catalog.category import Category


class CouponCategory(Model):
    """
    CouponCategory model
    
    Represents the coupon_category table in the OpenCart database.
    
    Attributes:
        coupon_id (int(11)) - Primary key
        category_id (int(11)) - Primary key
    """

    coupon_id = fields.IntField(null=True)
    category_id = fields.IntField(null=True)

    class Meta:
        table = "oc_coupon_category"
        unique_together = (("coupon_id", "category_id"),)

    async def get_coupon(self):
        """Get related Coupon"""
        if self.coupon_id:
            return await Coupon.get(coupon_id=self.coupon_id)
        return None
    async def get_category(self):
        """Get related Category"""
        if self.category_id:
            return await Category.get(category_id=self.category_id)
        return None
