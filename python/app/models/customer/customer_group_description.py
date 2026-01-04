"""
Tortoise ORM model for customer_group_description table
"""

from tortoise.models import Model
from tortoise import fields
from .customer_group import CustomerGroup
from ..localisation.language import Language


class CustomerGroupDescription(Model):
    """
    CustomerGroupDescription model
    
    Represents the customer_group_description table in the OpenCart database.
    
    Attributes:
        customer_group_id (int(11)) - Primary key
        language_id (int(11)) - Primary key
        name (varchar(32)), nullable
        description (text), nullable
    """

    customer_group_id = fields.IntField(null=True)
    language_id = fields.IntField(null=True)
    name = fields.CharField(max_length=32, null=True)
    description = fields.TextField(null=True)

    class Meta:
        table = "oc_customer_group_description"
        unique_together = (("customer_group_id", "language_id"),)

    async def get_customer_group(self):
        """Get related CustomerGroup"""
        if self.customer_group_id:
            return await CustomerGroup.get(customer_group_id=self.customer_group_id)
        return None
    async def get_language(self):
        """Get related Language"""
        if self.language_id:
            return await Language.get(language_id=self.language_id)
        return None
