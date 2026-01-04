"""
Tortoise ORM model for tax_rate_to_customer_group table
"""

from tortoise.models import Model
from tortoise import fields
from .tax_rate import TaxRate
from ..customer.customer_group import CustomerGroup


class TaxRateToCustomerGroup(Model):
    """
    TaxRateToCustomerGroup model
    
    Represents the tax_rate_to_customer_group table in the OpenCart database.
    
    Attributes:
        tax_rate_id (int(11)) - Primary key
        customer_group_id (int(11)) - Primary key
    """

    tax_rate_id = fields.IntField(null=True)
    customer_group_id = fields.IntField(null=True)

    class Meta:
        table = "oc_tax_rate_to_customer_group"
        unique_together = (("tax_rate_id", "customer_group_id"),)

    async def get_tax_rate(self):
        """Get related TaxRate"""
        if self.tax_rate_id:
            return await TaxRate.get(tax_rate_id=self.tax_rate_id)
        return None
    async def get_customer_group(self):
        """Get related CustomerGroup"""
        if self.customer_group_id:
            return await CustomerGroup.get(customer_group_id=self.customer_group_id)
        return None
