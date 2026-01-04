"""
Tortoise ORM model for product_subscription table
"""

from tortoise.models import Model
from tortoise import fields
from .product import Product
from .subscription_plan import SubscriptionPlan
from ..customer.customer_group import CustomerGroup


class ProductSubscription(Model):
    """
    ProductSubscription model
    
    Represents the product_subscription table in the OpenCart database.
    
    Attributes:
        product_id (int(11)) - Primary key
        subscription_plan_id (int(11)) - Primary key
        customer_group_id (int(11)) - Primary key
        trial_price (decimal(10,4)), nullable
        price (decimal(10,4)), nullable
    """

    product_id = fields.IntField(null=True)
    subscription_plan_id = fields.IntField(null=True)
    customer_group_id = fields.IntField(null=True)
    trial_price = fields.DecimalField(max_digits=10, decimal_places=4, null=True)
    price = fields.DecimalField(max_digits=10, decimal_places=4, null=True)

    class Meta:
        table = "oc_product_subscription"
        unique_together = (("product_id", "subscription_plan_id", "customer_group_id"),)

    async def get_product(self):
        """Get related Product"""
        if self.product_id:
            return await Product.get(product_id=self.product_id)
        return None
    async def get_subscription_plan(self):
        """Get related SubscriptionPlan"""
        if self.subscription_plan_id:
            return await SubscriptionPlan.get(subscription_plan_id=self.subscription_plan_id)
        return None
    async def get_customer_group(self):
        """Get related CustomerGroup"""
        if self.customer_group_id:
            return await CustomerGroup.get(customer_group_id=self.customer_group_id)
        return None
