"""
Tortoise ORM model for order_status table
"""

from tortoise.models import Model
from tortoise import fields
from ..localisation.language import Language


class OrderStatus(Model):
    """
    OrderStatus model
    
    Represents the order_status table in the OpenCart database.
    
    Attributes:
        order_status_id (int(11)) - Primary key
        language_id (int(11)) - Primary key
        name (varchar(32)), nullable
    """

    order_status_id = fields.IntField(null=True)
    language_id = fields.IntField(null=True)
    name = fields.CharField(max_length=32, null=True)

    class Meta:
        table = "oc_order_status"
        unique_together = (("order_status_id", "language_id"),)

    async def get_language(self):
        """Get related Language"""
        if self.language_id:
            return await Language.get(language_id=self.language_id)
        return None
