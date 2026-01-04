"""
Tortoise ORM model for antispam table
"""

from tortoise.models import Model
from tortoise import fields


class Antispam(Model):
    """
    Antispam model
    
    Represents the antispam table in the OpenCart database.
    
    Attributes:
        antispam_id (int(11)) - Primary key
        keyword (varchar(64)), nullable
    """

    antispam_id = fields.IntField(pk=True)
    keyword = fields.CharField(max_length=64, null=True)

    class Meta:
        table = "oc_antispam"
        indexes = [("keyword",)]

