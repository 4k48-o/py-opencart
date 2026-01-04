"""
Tortoise ORM model for cart table
"""

from tortoise.models import Model
from tortoise import fields
from ..system.store import Store
from ..customer.customer import Customer
from ..system.session import Session
from ..catalog.product import Product
from ..catalog.subscription_plan import SubscriptionPlan


class Cart(Model):
    """
    Cart model
    
    Represents the cart table in the OpenCart database.
    
    Attributes:
        cart_id (int(11)) - Primary key
        store_id (int(11)), nullable, default: 0
        customer_id (int(11)), nullable, default: 0
        session_id (varchar(32)), nullable
        product_id (int(11)), nullable
        subscription_plan_id (int(11)), nullable, default: 0
        option (text), nullable
        quantity (int(5)), nullable
        override (text), nullable
        price (decimal(15,4)), nullable
        date_added (datetime), nullable
    """

    cart_id = fields.IntField(pk=True)
    store_id = fields.IntField(null=True, default=0)
    customer_id = fields.IntField(null=True, default=0)
    session_id = fields.CharField(max_length=32, null=True)
    product_id = fields.IntField(null=True)
    subscription_plan_id = fields.IntField(null=True, default=0)
    option = fields.TextField(null=True)
    quantity = fields.IntField(null=True)
    override = fields.TextField(null=True)
    price = fields.DecimalField(max_digits=15, decimal_places=4, null=True)
    date_added = fields.DatetimeField(null=True)

    class Meta:
        table = "oc_cart"
        indexes = [("customer_id", "session_id", "product_id", "subscription_plan_id",)]

    async def get_store(self):
        """Get related Store"""
        if self.store_id:
            return await Store.get(store_id=self.store_id)
        return None
    async def get_customer(self):
        """Get related Customer"""
        if self.customer_id:
            return await Customer.get(customer_id=self.customer_id)
        return None
    async def get_session(self):
        """Get related Session"""
        if self.session_id:
            return await Session.get(session_id=self.session_id)
        return None
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
