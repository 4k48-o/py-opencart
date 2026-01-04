"""
Tortoise ORM model for return_history table
"""

from tortoise.models import Model
from tortoise import fields
from .return_status import ReturnStatus


class ReturnHistory(Model):
    """
    ReturnHistory model
    
    Represents the return_history table in the OpenCart database.
    
    Attributes:
        return_history_id (int(11)) - Primary key
        return_id (int(11)), nullable
        return_status_id (int(11)), nullable, default: 0
        notify (tinyint(1)), nullable
        comment (text), nullable
        date_added (datetime), nullable
    """

    return_history_id = fields.IntField(pk=True)
    return_id = fields.IntField(null=True)
    return_status_id = fields.IntField(null=True, default=0)
    notify = fields.SmallIntField(null=True)
    comment = fields.TextField(null=True)
    date_added = fields.DatetimeField(null=True)

    class Meta:
        table = "oc_return_history"

    async def get_return(self):
        """Get related Return"""
        if self.return_id:
            from importlib import import_module
            _module = import_module('app.models.system.return')
            Return = getattr(_module, 'Return')
            return await Return.get(return_id=self.return_id)
        return None
    async def get_return_status(self):
        """Get related ReturnStatus"""
        if self.return_status_id:
            return await ReturnStatus.get(return_status_id=self.return_status_id)
        return None
