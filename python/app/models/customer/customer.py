"""
Tortoise ORM model for customer table
"""

from tortoise.models import Model
from tortoise import fields
from .customer_group import CustomerGroup
from ..system.store import Store
from ..localisation.language import Language


class Customer(Model):
    """
    Customer model
    
    Represents the customer table in the OpenCart database.
    
    Attributes:
        customer_id (int(11)) - Primary key
        customer_group_id (int(11)), nullable, default: 0
        store_id (int(11)), nullable, default: 0
        language_id (int(11)), nullable, default: 0
        firstname (varchar(32)), nullable
        lastname (varchar(32)), nullable
        email (varchar(96)), nullable
        telephone (varchar(32)), nullable
        password (varchar(255)), nullable
        custom_field (text), nullable
        newsletter (tinyint(1)), nullable, default: 0
        ip (varchar(40)), nullable
        status (tinyint(1)), nullable, default: 0
        safe (tinyint(1)), nullable, default: 0
        commenter (tinyint(1)), nullable, default: 0
        token (text), nullable
        code (varchar(40)), nullable
        date_added (datetime), nullable
    """

    customer_id = fields.IntField(pk=True)
    customer_group_id = fields.IntField(null=True, default=0)
    store_id = fields.IntField(null=True, default=0)
    language_id = fields.IntField(null=True, default=0)
    firstname = fields.CharField(max_length=32, null=True)
    lastname = fields.CharField(max_length=32, null=True)
    email = fields.CharField(max_length=96, null=True)
    telephone = fields.CharField(max_length=32, null=True)
    password = fields.CharField(max_length=255, null=True)
    custom_field = fields.TextField(null=True)
    newsletter = fields.SmallIntField(null=True, default=0)
    ip = fields.CharField(max_length=40, null=True)
    status = fields.SmallIntField(null=True, default=0)
    safe = fields.SmallIntField(null=True, default=0)
    commenter = fields.SmallIntField(null=True, default=0)
    token = fields.TextField(null=True)
    code = fields.CharField(max_length=40, null=True)
    date_added = fields.DatetimeField(null=True)

    class Meta:
        table = "oc_customer"
        indexes = [("email",)]

    async def get_customer_group(self):
        """Get related CustomerGroup"""
        if self.customer_group_id:
            return await CustomerGroup.get(customer_group_id=self.customer_group_id)
        return None
    async def get_store(self):
        """Get related Store"""
        if self.store_id:
            return await Store.get(store_id=self.store_id)
        return None
    async def get_language(self):
        """Get related Language"""
        if self.language_id:
            return await Language.get(language_id=self.language_id)
        return None
