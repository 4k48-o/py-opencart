"""
Tortoise ORM model for subscription table
"""

from tortoise.models import Model
from tortoise import fields
from ..customer.customer import Customer
from ..order.order import Order
from ..order.order_product import OrderProduct
from ..catalog.subscription_plan import SubscriptionPlan
from ..localisation.subscription_status import SubscriptionStatus


class Subscription(Model):
    """
    Subscription model
    
    Represents the subscription table in the OpenCart database.
    
    Attributes:
        subscription_id (int(11)) - Primary key
        order_id (int(11)), nullable, default: 0
        store_id (int(11)), nullable, default: 0
        customer_id (int(11)), nullable
        payment_address_id (int(11)), nullable, default: 0
        payment_method (text), nullable
        shipping_address_id (int(11)), nullable, default: 0
        shipping_method (text), nullable
        subscription_plan_id (int(11)), nullable, default: 0
        trial_price (decimal(10,4)), nullable
        trial_tax (decimal(10,4)), nullable
        trial_frequency (enum(\), nullable
        trial_cycle (smallint(6)), nullable, default: 0
        trial_duration (smallint(6)), nullable, default: 0
        trial_remaining (smallint(6)), nullable, default: 0
        trial_status (tinyint(1)), nullable, default: 0
        price (decimal(10,4)), nullable
        tax (decimal(10,4)), nullable
        frequency (enum(\), nullable
        cycle (smallint(6)), nullable, default: 0
        duration (smallint(6)), nullable, default: 0
        remaining (smallint(6)), nullable, default: 0
        date_next (datetime), nullable
        comment (text), nullable
        subscription_status_id (int(11)), nullable, default: 0
        language (varchar(5)), nullable
        currency (varchar(3)), nullable
        date_added (datetime), nullable
        date_modified (datetime), nullable
    """

    subscription_id = fields.IntField(pk=True)
    order_id = fields.IntField(null=True, default=0)
    store_id = fields.IntField(null=True, default=0)
    customer_id = fields.IntField(null=True)
    payment_address_id = fields.IntField(null=True, default=0)
    payment_method = fields.TextField(null=True)
    shipping_address_id = fields.IntField(null=True, default=0)
    shipping_method = fields.TextField(null=True)
    subscription_plan_id = fields.IntField(null=True, default=0)
    trial_price = fields.DecimalField(max_digits=10, decimal_places=4, null=True)
    trial_tax = fields.DecimalField(max_digits=10, decimal_places=4, null=True)
    trial_frequency = fields.CharField(max_length=32, null=True)
    trial_cycle = fields.SmallIntField(null=True, default=0)
    trial_duration = fields.SmallIntField(null=True, default=0)
    trial_remaining = fields.SmallIntField(null=True, default=0)
    trial_status = fields.SmallIntField(null=True, default=0)
    price = fields.DecimalField(max_digits=10, decimal_places=4, null=True)
    tax = fields.DecimalField(max_digits=10, decimal_places=4, null=True)
    frequency = fields.CharField(max_length=32, null=True)
    cycle = fields.SmallIntField(null=True, default=0)
    duration = fields.SmallIntField(null=True, default=0)
    remaining = fields.SmallIntField(null=True, default=0)
    date_next = fields.DatetimeField(null=True)
    comment = fields.TextField(null=True)
    subscription_status_id = fields.IntField(null=True, default=0)
    language = fields.CharField(max_length=5, null=True)
    currency = fields.CharField(max_length=3, null=True)
    date_added = fields.DatetimeField(null=True)
    date_modified = fields.DatetimeField(null=True)

    class Meta:
        table = "oc_subscription"
        indexes = [("order_id",)]

    async def get_customer(self):
        """Get related Customer"""
        if self.customer_id:
            return await Customer.get(customer_id=self.customer_id)
        return None
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
