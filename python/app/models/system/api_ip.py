"""
Tortoise ORM model for api_ip table
"""

from tortoise.models import Model
from tortoise import fields
from .api import Api


class ApiIp(Model):
    """
    ApiIp model
    
    Represents the api_ip table in the OpenCart database.
    
    Attributes:
        api_ip_id (int(11)) - Primary key
        api_id (int(11)), nullable
        ip (varchar(40)), nullable
    """

    api_ip_id = fields.IntField(pk=True)
    api_id = fields.IntField(null=True)
    ip = fields.CharField(max_length=40, null=True)

    class Meta:
        table = "oc_api_ip"

    async def get_api(self):
        """Get related Api"""
        if self.api_id:
            return await Api.get(api_id=self.api_id)
        return None
