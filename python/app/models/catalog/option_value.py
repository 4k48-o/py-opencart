"""
Tortoise ORM model for option_value table
"""

from tortoise.models import Model
from tortoise import fields
from .option import Option


class OptionValue(Model):
    """
    OptionValue model
    
    Represents the option_value table in the OpenCart database.
    
    Attributes:
        option_value_id (int(11)) - Primary key
        option_id (int(11)), nullable
        image (varchar(255)), nullable
        sort_order (int(3)), nullable, default: 0
    """

    option_value_id = fields.IntField(pk=True)
    option_id = fields.IntField(null=True)
    image = fields.CharField(max_length=255, null=True)
    sort_order = fields.IntField(null=True, default=0)

    class Meta:
        table = "oc_option_value"

    async def get_option(self):
        """Get related Option"""
        if self.option_id:
            return await Option.get(option_id=self.option_id)
        return None
