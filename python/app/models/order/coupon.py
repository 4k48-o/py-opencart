"""
Tortoise ORM model for coupon table
"""

from tortoise.models import Model
from tortoise import fields


class Coupon(Model):
    """
    Coupon model
    
    Represents the coupon table in the OpenCart database.
    
    Attributes:
        coupon_id (int(11)) - Primary key
        name (varchar(128)), nullable
        code (varchar(20)), nullable
        type (char(1)), nullable
        discount (decimal(15,4)), nullable
        logged (tinyint(1)), nullable, default: 0
        shipping (tinyint(1)), nullable, default: 0
        total (decimal(15,4)), nullable
        date_start (date), nullable
        date_end (date), nullable
        uses_total (int(11)), nullable, default: 0
        uses_customer (int(11)), nullable, default: 0
        status (tinyint(1)), nullable, default: 0
        date_added (datetime), nullable
    """

    coupon_id = fields.IntField(pk=True)
    name = fields.CharField(max_length=128, null=True)
    code = fields.CharField(max_length=20, null=True)
    type = fields.CharField(max_length=1, null=True)
    discount = fields.DecimalField(max_digits=15, decimal_places=4, null=True)
    logged = fields.SmallIntField(null=True, default=0)
    shipping = fields.SmallIntField(null=True, default=0)
    total = fields.DecimalField(max_digits=15, decimal_places=4, null=True)
    date_start = fields.DateField(null=True)
    date_end = fields.DateField(null=True)
    uses_total = fields.IntField(null=True, default=0)
    uses_customer = fields.IntField(null=True, default=0)
    status = fields.SmallIntField(null=True, default=0)
    date_added = fields.DatetimeField(null=True)

    class Meta:
        table = "oc_coupon"

