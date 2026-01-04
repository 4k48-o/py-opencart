"""
Tortoise ORM model for coupon_history table
"""

from tortoise.models import Model
from tortoise import fields
from .coupon import Coupon
from .order import Order
from ..customer.customer import Customer


class CouponHistory(Model):
    """
    CouponHistory model
    
    Represents the coupon_history table in the OpenCart database.
    
    Attributes:
        coupon_history_id (int(11)) - Primary key
        coupon_id (int(11)), nullable
        order_id (int(11)), nullable, default: 0
        customer_id (int(11)), nullable, default: 0
        amount (decimal(15,4)), nullable
        date_added (datetime), nullable
    """

    coupon_history_id = fields.IntField(pk=True)
    coupon_id = fields.IntField(null=True)
    order_id = fields.IntField(null=True, default=0)
    customer_id = fields.IntField(null=True, default=0)
    amount = fields.DecimalField(max_digits=15, decimal_places=4, null=True)
    date_added = fields.DatetimeField(null=True)

    class Meta:
        table = "oc_coupon_history"

    async def get_coupon(self):
        """Get related Coupon"""
        if self.coupon_id:
            return await Coupon.get(coupon_id=self.coupon_id)
        return None
    async def get_order(self):
        """Get related Order"""
        if self.order_id:
            return await Order.get(order_id=self.order_id)
        return None
    async def get_customer(self):
        """Get related Customer"""
        if self.customer_id:
            return await Customer.get(customer_id=self.customer_id)
        return None
