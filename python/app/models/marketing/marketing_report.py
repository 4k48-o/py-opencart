"""
Tortoise ORM model for marketing_report table
"""

from tortoise.models import Model
from tortoise import fields
from .marketing import Marketing
from ..system.store import Store


class MarketingReport(Model):
    """
    MarketingReport model
    
    Represents the marketing_report table in the OpenCart database.
    
    Attributes:
        marketing_report_id (int(11)) - Primary key
        marketing_id (int(11)), nullable
        store_id (int(11)), nullable, default: 0
        ip (varchar(40)), nullable
        country (varchar(2)), nullable
        date_added (datetime), nullable
    """

    marketing_report_id = fields.IntField(pk=True)
    marketing_id = fields.IntField(null=True)
    store_id = fields.IntField(null=True, default=0)
    ip = fields.CharField(max_length=40, null=True)
    country = fields.CharField(max_length=2, null=True)
    date_added = fields.DatetimeField(null=True)

    class Meta:
        table = "oc_marketing_report"

    async def get_marketing(self):
        """Get related Marketing"""
        if self.marketing_id:
            return await Marketing.get(marketing_id=self.marketing_id)
        return None
    async def get_store(self):
        """Get related Store"""
        if self.store_id:
            return await Store.get(store_id=self.store_id)
        return None
