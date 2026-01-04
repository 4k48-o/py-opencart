"""
Tortoise ORM model for api_history table
"""

from tortoise.models import Model
from tortoise import fields
from .api import Api


class ApiHistory(Model):
    """
    ApiHistory model
    
    Represents the api_history table in the OpenCart database.
    
    Attributes:
        api_history_id (int(11)) - Primary key
        api_id (int(11)), nullable
        call (varchar(32)), nullable
        ip (varchar(40)), nullable
        date_added (datetime), nullable
    """

    api_history_id = fields.IntField(pk=True)
    api_id = fields.IntField(null=True)
    call = fields.CharField(max_length=32, null=True)
    ip = fields.CharField(max_length=40, null=True)
    date_added = fields.DatetimeField(null=True)

    class Meta:
        table = "oc_api_history"

    async def get_api(self):
        """Get related Api"""
        if self.api_id:
            return await Api.get(api_id=self.api_id)
        return None
