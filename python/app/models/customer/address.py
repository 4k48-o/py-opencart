"""
Tortoise ORM model for address table
"""

from tortoise.models import Model
from tortoise import fields
from .customer import Customer


class Address(Model):
    """
    Address model
    
    Represents the address table in the OpenCart database.
    
    Attributes:
        address_id (int(11)) - Primary key
        customer_id (int(11)), nullable
        firstname (varchar(32)), nullable
        lastname (varchar(32)), nullable
        company (varchar(60)), nullable
        address_1 (varchar(128)), nullable
        address_2 (varchar(128)), nullable
        city (varchar(128)), nullable
        postcode (varchar(10)), nullable
        country_id (int(11)), nullable, default: 0
        zone_id (int(11)), nullable, default: 0
        custom_field (text), nullable
        is_default (tinyint(1)), nullable, default: 0
    """

    address_id = fields.IntField(pk=True)
    customer_id = fields.IntField(null=True)
    firstname = fields.CharField(max_length=32, null=True)
    lastname = fields.CharField(max_length=32, null=True)
    company = fields.CharField(max_length=60, null=True)
    address_1 = fields.CharField(max_length=128, null=True)
    address_2 = fields.CharField(max_length=128, null=True)
    city = fields.CharField(max_length=128, null=True)
    postcode = fields.CharField(max_length=10, null=True)
    country_id = fields.IntField(null=True, default=0)
    zone_id = fields.IntField(null=True, default=0)
    custom_field = fields.TextField(null=True)
    # OpenCart 数据库表中字段名是 'default' 而不是 'is_default'
    default = fields.SmallIntField(null=True, default=0, source_field="default")

    class Meta:
        table = "oc_address"
        indexes = [("customer_id",)]

    async def get_customer(self):
        """Get related Customer"""
        if self.customer_id:
            return await Customer.get(customer_id=self.customer_id)
        return None
