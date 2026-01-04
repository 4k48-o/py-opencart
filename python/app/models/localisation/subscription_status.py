"""
Tortoise ORM model for subscription_status table
"""

from tortoise.models import Model
from tortoise import fields
from .language import Language


class SubscriptionStatus(Model):
    """
    SubscriptionStatus model
    
    Represents the subscription_status table in the OpenCart database.
    
    Attributes:
        subscription_status_id (int(11)) - Primary key
        language_id (int(11)) - Primary key
        name (varchar(32)), nullable
    """

    subscription_status_id = fields.IntField(null=True)
    language_id = fields.IntField(null=True)
    name = fields.CharField(max_length=32, null=True)

    class Meta:
        table = "oc_subscription_status"
        unique_together = (("subscription_status_id", "language_id"),)

    async def get_language(self):
        """Get related Language"""
        if self.language_id:
            return await Language.get(language_id=self.language_id)
        return None
