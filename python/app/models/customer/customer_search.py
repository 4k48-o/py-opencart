"""
Tortoise ORM model for customer_search table
"""

from tortoise.models import Model
from tortoise import fields
from ..system.store import Store
from ..localisation.language import Language
from .customer import Customer
from ..catalog.category import Category


class CustomerSearch(Model):
    """
    CustomerSearch model
    
    Represents the customer_search table in the OpenCart database.
    
    Attributes:
        customer_search_id (int(11)) - Primary key
        store_id (int(11)), nullable, default: 0
        language_id (int(11)), nullable
        customer_id (int(11)), nullable, default: 0
        keyword (varchar(255)), nullable
        category_id (int(11)), nullable
        sub_category (tinyint(1)), nullable
        description (tinyint(1)), nullable
        products (int(11)), nullable
        ip (varchar(40)), nullable
        date_added (datetime), nullable
    """

    customer_search_id = fields.IntField(pk=True)
    store_id = fields.IntField(null=True, default=0)
    language_id = fields.IntField(null=True)
    customer_id = fields.IntField(null=True, default=0)
    keyword = fields.CharField(max_length=255, null=True)
    category_id = fields.IntField(null=True)
    sub_category = fields.SmallIntField(null=True)
    description = fields.SmallIntField(null=True)
    products = fields.IntField(null=True)
    ip = fields.CharField(max_length=40, null=True)
    date_added = fields.DatetimeField(null=True)

    class Meta:
        table = "oc_customer_search"

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
    async def get_customer(self):
        """Get related Customer"""
        if self.customer_id:
            return await Customer.get(customer_id=self.customer_id)
        return None
    async def get_category(self):
        """Get related Category"""
        if self.category_id:
            return await Category.get(category_id=self.category_id)
        return None
