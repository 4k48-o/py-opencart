"""
Tortoise ORM model for tax_rule table
"""

from tortoise.models import Model
from tortoise import fields
from .tax_class import TaxClass
from .tax_rate import TaxRate


class TaxRule(Model):
    """
    TaxRule model
    
    Represents the tax_rule table in the OpenCart database.
    
    Attributes:
        tax_rule_id (int(11)) - Primary key
        tax_class_id (int(11)), nullable
        tax_rate_id (int(11)), nullable
        based (varchar(10)), nullable
        priority (int(5)), nullable, default: 1
    """

    tax_rule_id = fields.IntField(pk=True)
    tax_class_id = fields.IntField(null=True)
    tax_rate_id = fields.IntField(null=True)
    based = fields.CharField(max_length=10, null=True)
    priority = fields.IntField(null=True, default=1)

    class Meta:
        table = "oc_tax_rule"

    async def get_tax_class(self):
        """Get related TaxClass"""
        if self.tax_class_id:
            return await TaxClass.get(tax_class_id=self.tax_class_id)
        return None
    async def get_tax_rate(self):
        """Get related TaxRate"""
        if self.tax_rate_id:
            return await TaxRate.get(tax_rate_id=self.tax_rate_id)
        return None
