"""
Tortoise ORM model for subscription_product table
"""

from tortoise.models import Model
from tortoise import fields
from .subscription import Subscription
from ..catalog.product import Product


class SubscriptionProduct(Model):
    """
    SubscriptionProduct model
    
    Represents the subscription_product table in the OpenCart database.
    
    Attributes:
        subscription_product_id (int(11)) - Primary key
        subscription_id (int(11)), nullable
        order_id (int(11)), nullable, default: 0
        order_product_id (int(11)), nullable, default: 0
        product_id (int(11)), nullable
        name (varchar(255)), nullable
        model (varchar(255)), nullable
        quantity (int(4)), nullable, default: 0
        trial_price (decimal(10,4)), nullable
        trial_tax (decimal(15,4)), nullable, default: 0.0000
        price (decimal(10,4)), nullable
        tax (decimal(15,4)), nullable, default: 0.0000
    """

    subscription_product_id = fields.IntField(pk=True)
    subscription_id = fields.IntField(null=True)
    order_id = fields.IntField(null=True, default=0)
    order_product_id = fields.IntField(null=True, default=0)
    product_id = fields.IntField(null=True)
    name = fields.CharField(max_length=255, null=True)
    model = fields.CharField(max_length=255, null=True)
    quantity = fields.IntField(null=True, default=0)
    trial_price = fields.DecimalField(max_digits=10, decimal_places=4, null=True)
    trial_tax = fields.DecimalField(max_digits=15, decimal_places=4, null=True, default='0.0000')
    price = fields.DecimalField(max_digits=10, decimal_places=4, null=True)
    tax = fields.DecimalField(max_digits=15, decimal_places=4, null=True, default='0.0000')

    class Meta:
        table = "oc_subscription_product"
        indexes = [("subscription_id",)]

    async def get_subscription(self):
        """Get related Subscription"""
        if self.subscription_id:
            return await Subscription.get(subscription_id=self.subscription_id)
        return None
    async def get_product(self):
        """Get related Product"""
        if self.product_id:
            return await Product.get(product_id=self.product_id)
        return None
