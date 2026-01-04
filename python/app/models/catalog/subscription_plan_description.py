"""
Tortoise ORM model for subscription_plan_description table
"""

from tortoise.models import Model
from tortoise import fields
from ..localisation.language import Language


class SubscriptionPlanDescription(Model):
    """
    SubscriptionPlanDescription model
    
    Represents the subscription_plan_description table in the OpenCart database.
    
    Attributes:
        subscription_plan_id (int(11)) - Primary key
        language_id (int(11)) - Primary key
        name (varchar(255)), nullable
    """

    subscription_plan_id = fields.IntField(null=True)
    language_id = fields.IntField(null=True)
    name = fields.CharField(max_length=255, null=True)

    class Meta:
        table = "oc_subscription_plan_description"
        unique_together = (("subscription_plan_id", "language_id"),)

    async def get_language(self):
        """Get related Language"""
        if self.language_id:
            return await Language.get(language_id=self.language_id)
        return None
