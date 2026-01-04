"""
Tortoise ORM model for return_reason table
"""

from tortoise.models import Model
from tortoise import fields
from .language import Language


class ReturnReason(Model):
    """
    ReturnReason model
    
    Represents the return_reason table in the OpenCart database.
    
    Attributes:
        return_reason_id (int(11)) - Primary key
        language_id (int(11)) - Primary key, default: 0
        name (varchar(128)), nullable
    """

    return_reason_id = fields.IntField(null=True)
    language_id = fields.IntField(null=True, default=0)
    name = fields.CharField(max_length=128, null=True)

    class Meta:
        table = "oc_return_reason"
        unique_together = (("return_reason_id", "language_id"),)

    async def get_language(self):
        """Get related Language"""
        if self.language_id:
            return await Language.get(language_id=self.language_id)
        return None
