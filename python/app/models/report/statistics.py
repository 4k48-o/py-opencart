"""
Tortoise ORM model for statistics table
"""

from tortoise.models import Model
from tortoise import fields


class Statistics(Model):
    """
    Statistics model
    
    Represents the statistics table in the OpenCart database.
    
    Attributes:
        statistics_id (int(11)) - Primary key
        code (varchar(64)), nullable
        value (decimal(15,4)), nullable
    """

    statistics_id = fields.IntField(pk=True)
    code = fields.CharField(max_length=64, null=True)
    value = fields.DecimalField(max_digits=15, decimal_places=4, null=True)

    class Meta:
        table = "oc_statistics"

