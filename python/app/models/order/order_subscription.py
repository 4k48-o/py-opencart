"""
Tortoise ORM model for order_subscription table
"""

from tortoise.models import Model
from tortoise import fields
from .order import Order
from .order_product import OrderProduct
from ..catalog.subscription_plan import SubscriptionPlan
from ..localisation.subscription_status import SubscriptionStatus


class OrderSubscription(Model):
    """
    OrderSubscription model
    
    Represents the order_subscription table in the OpenCart database.
    
    Attributes:
        order_subscription_id (int(11)) - Primary key
        order_product_id (int(11)), nullable
        order_id (int(11)), nullable
        product_id (int(11)), nullable
        quantity (int(4)), nullable, default: 1
        subscription_plan_id (int(11)), nullable
        trial_price (decimal(10,4)), nullable
        trial_tax (decimal(15,4)), nullable
        trial_frequency (enum(\), nullable
        trial_cycle (smallint(6)), nullable
        trial_duration (smallint(6)), nullable
        trial_status (tinyint(1)), nullable, default: 0
        price (decimal(10,4)), nullable
        tax (decimal(15,4)), nullable
        frequency (enum(\), nullable
        cycle (smallint(6)), nullable, default: 1
        duration (smallint(6)), nullable, default: 0
    """

    order_subscription_id = fields.IntField(pk=True)
    order_product_id = fields.IntField(null=True)
    order_id = fields.IntField(null=True)
    product_id = fields.IntField(null=True)
    quantity = fields.IntField(null=True, default=1)
    subscription_plan_id = fields.IntField(null=True)
    trial_price = fields.DecimalField(max_digits=10, decimal_places=4, null=True)
    trial_tax = fields.DecimalField(max_digits=15, decimal_places=4, null=True)
    trial_frequency = fields.CharField(max_length=32, null=True)
    trial_cycle = fields.SmallIntField(null=True)
    trial_duration = fields.SmallIntField(null=True)
    trial_status = fields.SmallIntField(null=True, default=0)
    price = fields.DecimalField(max_digits=10, decimal_places=4, null=True)
    tax = fields.DecimalField(max_digits=15, decimal_places=4, null=True)
    frequency = fields.CharField(max_length=32, null=True)
    cycle = fields.SmallIntField(null=True, default=1)
    duration = fields.SmallIntField(null=True, default=0)

    class Meta:
        table = "oc_order_subscription"
        indexes = [("order_id",)]

    async def get_order(self):
        """Get related Order"""
        if self.order_id:
            return await Order.get(order_id=self.order_id)
        return None
    async def get_order_product(self):
        """Get related OrderProduct"""
        if self.order_product_id:
            return await OrderProduct.get(order_product_id=self.order_product_id)
        return None
    async def get_subscription_plan(self):
        """Get related SubscriptionPlan"""
        if self.subscription_plan_id:
            return await SubscriptionPlan.get(subscription_plan_id=self.subscription_plan_id)
        return None
    async def get_subscription_status(self):
        """Get related SubscriptionStatus"""
        if self.subscription_status_id:
            return await SubscriptionStatus.get(subscription_status_id=self.subscription_status_id)
        return None
