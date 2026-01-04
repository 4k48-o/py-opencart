"""
Tortoise ORM model for return_status table
"""

from tortoise.models import Model
from tortoise import fields
from .language import Language


class ReturnStatus(Model):
    """
    ReturnStatus model
    
    Represents the return_status table in the OpenCart database.
    
    Attributes:
        return_status_id (int(11)) - Primary key
        language_id (int(11)) - Primary key, default: 0
        name (varchar(32)), nullable
    """

    return_status_id = fields.IntField(null=True)
    language_id = fields.IntField(null=True, default=0)
    name = fields.CharField(max_length=32, null=True)

    class Meta:
        table = "oc_return_status"
        unique_together = (("return_status_id", "language_id"),)

    async def get_language(self):
        """Get related Language"""
        if self.language_id:
            return await Language.get(language_id=self.language_id)
        return None
