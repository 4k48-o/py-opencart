"""
Tortoise ORM model for subscription_log table
"""

from tortoise.models import Model
from tortoise import fields
from .subscription import Subscription


class SubscriptionLog(Model):
    """
    SubscriptionLog model
    
    Represents the subscription_log table in the OpenCart database.
    
    Attributes:
        subscription_log_id (int(11)) - Primary key
        subscription_id (int(11)), nullable
        code (varchar(128)), nullable
        description (text), nullable
        status (tinyint(1)), nullable, default: 0
        date_added (datetime), nullable
    """

    subscription_log_id = fields.IntField(pk=True)
    subscription_id = fields.IntField(null=True)
    code = fields.CharField(max_length=128, null=True)
    description = fields.TextField(null=True)
    status = fields.SmallIntField(null=True, default=0)
    date_added = fields.DatetimeField(null=True)

    class Meta:
        table = "oc_subscription_log"

    async def get_subscription(self):
        """Get related Subscription"""
        if self.subscription_id:
            return await Subscription.get(subscription_id=self.subscription_id)
        return None
