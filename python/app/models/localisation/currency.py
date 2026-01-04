"""
Tortoise ORM model for currency table
"""

from tortoise.models import Model
from tortoise import fields


class Currency(Model):
    """
    Currency model
    
    Represents the currency table in the OpenCart database.
    
    Attributes:
        currency_id (int(11)) - Primary key
        title (varchar(32)), nullable
        code (varchar(3)), nullable
        symbol_left (varchar(12)), nullable
        symbol_right (varchar(12)), nullable
        decimal_place (int(1)), nullable, default: 2
        value (double(15,8)), nullable
        status (tinyint(1)), nullable, default: 0
        date_modified (datetime), nullable
    """

    currency_id = fields.IntField(pk=True)
    title = fields.CharField(max_length=32, null=True)
    code = fields.CharField(max_length=3, null=True)
    symbol_left = fields.CharField(max_length=12, null=True)
    symbol_right = fields.CharField(max_length=12, null=True)
    decimal_place = fields.IntField(null=True, default=2)
    value = fields.FloatField(null=True)
    status = fields.SmallIntField(null=True, default=0)
    date_modified = fields.DatetimeField(null=True)

    class Meta:
        table = "oc_currency"

