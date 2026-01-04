"""
Tortoise ORM model for custom_field_customer_group table
"""

from tortoise.models import Model
from tortoise import fields
from .custom_field import CustomField
from ..customer.customer_group import CustomerGroup


class CustomFieldCustomerGroup(Model):
    """
    CustomFieldCustomerGroup model
    
    Represents the custom_field_customer_group table in the OpenCart database.
    
    Attributes:
        custom_field_id (int(11)) - Primary key
        customer_group_id (int(11)) - Primary key
        required (tinyint(1)), nullable, default: 0
    """

    custom_field_id = fields.IntField(null=True)
    customer_group_id = fields.IntField(null=True)
    required = fields.SmallIntField(null=True, default=0)

    class Meta:
        table = "oc_custom_field_customer_group"
        unique_together = (("custom_field_id", "customer_group_id"),)

    async def get_custom_field(self):
        """Get related CustomField"""
        if self.custom_field_id:
            return await CustomField.get(custom_field_id=self.custom_field_id)
        return None
    async def get_customer_group(self):
        """Get related CustomerGroup"""
        if self.customer_group_id:
            return await CustomerGroup.get(customer_group_id=self.customer_group_id)
        return None
