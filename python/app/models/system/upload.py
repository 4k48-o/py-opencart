"""
Tortoise ORM model for upload table
"""

from tortoise.models import Model
from tortoise import fields


class Upload(Model):
    """
    Upload model
    
    Represents the upload table in the OpenCart database.
    
    Attributes:
        upload_id (int(11)) - Primary key
        name (varchar(255)), nullable
        filename (varchar(255)), nullable
        code (varchar(255)), nullable
        date_added (datetime), nullable
    """

    upload_id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255, null=True)
    filename = fields.CharField(max_length=255, null=True)
    code = fields.CharField(max_length=255, null=True)
    date_added = fields.DatetimeField(null=True)

    class Meta:
        table = "oc_upload"

