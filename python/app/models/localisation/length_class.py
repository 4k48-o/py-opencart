"""
Tortoise ORM model for length_class table
"""

from tortoise.models import Model
from tortoise import fields


class LengthClass(Model):
    """
    LengthClass model
    
    Represents the length_class table in the OpenCart database.
    
    Attributes:
        length_class_id (int(11)) - Primary key
        value (decimal(15,8)), nullable
    """

    length_class_id = fields.IntField(pk=True)
    value = fields.DecimalField(max_digits=15, decimal_places=8, null=True)

    class Meta:
        table = "oc_length_class"

