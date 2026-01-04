"""
Tortoise ORM model for subscription_history table
"""

from tortoise.models import Model
from tortoise import fields
from .subscription import Subscription
from ..localisation.subscription_status import SubscriptionStatus


class SubscriptionHistory(Model):
    """
    SubscriptionHistory model
    
    Represents the subscription_history table in the OpenCart database.
    
    Attributes:
        subscription_history_id (int(11)) - Primary key
        subscription_id (int(11)), nullable
        subscription_status_id (int(11)), nullable, default: 0
        notify (tinyint(1)), nullable, default: 0
        comment (text), nullable
        date_added (datetime), nullable
    """

    subscription_history_id = fields.IntField(pk=True)
    subscription_id = fields.IntField(null=True)
    subscription_status_id = fields.IntField(null=True, default=0)
    notify = fields.SmallIntField(null=True, default=0)
    comment = fields.TextField(null=True)
    date_added = fields.DatetimeField(null=True)

    class Meta:
        table = "oc_subscription_history"

    async def get_subscription(self):
        """Get related Subscription"""
        if self.subscription_id:
            return await Subscription.get(subscription_id=self.subscription_id)
        return None
    async def get_subscription_status(self):
        """Get related SubscriptionStatus"""
        if self.subscription_status_id:
            return await SubscriptionStatus.get(subscription_status_id=self.subscription_status_id)
        return None
