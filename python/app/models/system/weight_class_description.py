"""
Tortoise ORM model for weight_class_description table
"""

from tortoise.models import Model
from tortoise import fields
from ..localisation.language import Language


class WeightClassDescription(Model):
    """
    WeightClassDescription model
    
    Represents the weight_class_description table in the OpenCart database.
    
    Attributes:
        weight_class_id (int(11)) - Primary key
        language_id (int(11)) - Primary key
        title (varchar(32)), nullable
        unit (varchar(4)), nullable
    """

    weight_class_id = fields.IntField(null=True)
    language_id = fields.IntField(null=True)
    title = fields.CharField(max_length=32, null=True)
    unit = fields.CharField(max_length=4, null=True)

    class Meta:
        table = "oc_weight_class_description"
        unique_together = (("weight_class_id", "language_id"),)

    async def get_language(self):
        """Get related Language"""
        if self.language_id:
            return await Language.get(language_id=self.language_id)
        return None
