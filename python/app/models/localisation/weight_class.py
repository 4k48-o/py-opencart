"""
Tortoise ORM model for weight_class table
"""

from tortoise.models import Model
from tortoise import fields


class WeightClass(Model):
    """
    WeightClass model
    
    Represents the weight_class table in the OpenCart database.
    
    Attributes:
        weight_class_id (int(11)) - Primary key
        value (decimal(15,8)), nullable, default: 0.00000000
    """

    weight_class_id = fields.IntField(pk=True)
    value = fields.DecimalField(max_digits=15, decimal_places=8, null=True, default='0.00000000')

    class Meta:
        table = "oc_weight_class"

