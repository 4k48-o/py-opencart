"""
Tortoise ORM model for subscription_option table
"""

from tortoise.models import Model
from tortoise import fields
from .subscription import Subscription
from .subscription_product import SubscriptionProduct
from ..catalog.product_option import ProductOption
from ..catalog.product_option_value import ProductOptionValue


class SubscriptionOption(Model):
    """
    SubscriptionOption model
    
    Represents the subscription_option table in the OpenCart database.
    
    Attributes:
        subscription_option_id (int(11)) - Primary key
        subscription_id (int(11)), nullable
        subscription_product_id (int(11)), nullable
        product_option_id (int(11)), nullable
        product_option_value_id (int(11)), nullable, default: 0
        name (varchar(255)), nullable
        value (text), nullable
        type (varchar(32)), nullable
    """

    subscription_option_id = fields.IntField(pk=True)
    subscription_id = fields.IntField(null=True)
    subscription_product_id = fields.IntField(null=True)
    product_option_id = fields.IntField(null=True)
    product_option_value_id = fields.IntField(null=True, default=0)
    name = fields.CharField(max_length=255, null=True)
    value = fields.TextField(null=True)
    type = fields.CharField(max_length=32, null=True)

    class Meta:
        table = "oc_subscription_option"

    async def get_subscription(self):
        """Get related Subscription"""
        if self.subscription_id:
            return await Subscription.get(subscription_id=self.subscription_id)
        return None
    async def get_subscription_product(self):
        """Get related SubscriptionProduct"""
        if self.subscription_product_id:
            return await SubscriptionProduct.get(subscription_product_id=self.subscription_product_id)
        return None
    async def get_product_option(self):
        """Get related ProductOption"""
        if self.product_option_id:
            return await ProductOption.get(product_option_id=self.product_option_id)
        return None
    async def get_product_option_value(self):
        """Get related ProductOptionValue"""
        if self.product_option_value_id:
            return await ProductOptionValue.get(product_option_value_id=self.product_option_value_id)
        return None
