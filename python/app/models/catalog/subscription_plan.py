"""
Tortoise ORM model for subscription_plan table
"""

from tortoise.models import Model
from tortoise import fields


class SubscriptionPlan(Model):
    """
    SubscriptionPlan model
    
    Represents the subscription_plan table in the OpenCart database.
    
    Attributes:
        subscription_plan_id (int(11)) - Primary key
        trial_frequency (enum(\), nullable
        trial_duration (int(10)), nullable, default: 0
        trial_cycle (int(10)), nullable, default: 0
        trial_status (tinyint(4)), nullable, default: 0
        frequency (enum(\), nullable
        duration (int(10)), nullable, default: 0
        cycle (int(10)), nullable, default: 0
        status (tinyint(1)), nullable, default: 0
        sort_order (int(3)), nullable, default: 0
    """

    subscription_plan_id = fields.IntField(pk=True)
    trial_frequency = fields.CharField(max_length=32, null=True)
    trial_duration = fields.IntField(null=True, default=0)
    trial_cycle = fields.IntField(null=True, default=0)
    trial_status = fields.SmallIntField(null=True, default=0)
    frequency = fields.CharField(max_length=32, null=True)
    duration = fields.IntField(null=True, default=0)
    cycle = fields.IntField(null=True, default=0)
    status = fields.SmallIntField(null=True, default=0)
    sort_order = fields.IntField(null=True, default=0)

    class Meta:
        table = "oc_subscription_plan"

